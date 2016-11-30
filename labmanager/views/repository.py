import json
import hashlib
from flask import Blueprint, jsonify, url_for, request, current_app, Response, render_template_string, redirect

from dict2xml import dict2xml

from labmanager.db import db
from labmanager.models import RLMS, Laboratory, EmbedApplication
from labmanager.rlms import get_manager_class, Capabilities
from labmanager.rlms.caches import force_cache

repository_blueprint = Blueprint('repository', __name__)

@repository_blueprint.before_request
def requires_lms_auth():
    shared_secret = current_app.config.get('REPOSITORY_SHARED_SECRET')
    if not shared_secret:
        return

    UNAUTHORIZED = Response(response="Could not verify your credentials", status=401, headers = {'WWW-Authenticate':'Basic realm="Login Required"'})

    auth = request.authorization
    if not auth:
        return UNAUTHORIZED
    else:
        password = auth.password

    if password != shared_secret:
        return UNAUTHORIZED

@repository_blueprint.route('/')
def index():
    return "Welcome to the repository"

def create_lab_id(rlms, laboratory_id, single = True):
    # not single since we were using single = True in the past for all of them (and majority are not single)
    identifier = 'lab:rlms={};lab={};{}'.format(rlms.id, laboratory_id, not single)
    return hashlib.new('sha1', identifier).hexdigest()

def create_app_id(app):
    identifier = '{}'.format(app.id)
    return hashlib.new('sha1', identifier).hexdigest()

def lab_to_json(lab, widgets, rlms, single, age_ranges, domains):
    age_ranges = lab.age_ranges or age_ranges or [] # e.g., 12-13, 14-15
    domains = lab.domains or domains or [] # e.g., Physics, Chemistry
    lab_widgets = []
    for widget in widgets:
        lab_widgets.append({
            'app_url': widget['link'],
            'app_title': widget['name'],
            'external_url': widget['external'],
        })
    return {
            'id': create_lab_id(rlms, lab.laboratory_id, single),
            'title': lab.name,
            'description': lab.description or '',
            'domains' : domains,
            'age_range' : age_ranges,
            'lab_apps' : lab_widgets,
            'keywords' : lab.keywords or []
        }

def app_to_json(embed_app):
    age_ranges = embed_app.age_ranges # e.g., 12-13, 14-15
    domains = embed_app.domains # e.g., Physics, Chemistry
    lab_widgets = [{
        'app_url': url_for('embed.app_xml', identifier=embed_app.identifier, _external=True),
        'app_title': embed_app.name,
    }]
    return {
            'id':  create_app_id(embed_app),
            'title': embed_app.name,
            'description': embed_app.description or '',
            'domains' : domains,
            'age_range' : age_ranges,
            'lab_apps' : lab_widgets,
            'keywords' : []
        }

def lab_to_xml(lab, widgets, rlms, single, age_ranges, domains):
    age_ranges = lab.age_ranges or age_ranges or [] # e.g., 12-13, 14-15
    domains = lab.domains or domains or [] # e.g., Physics, Chemistry
    lab_widgets = []
    for widget in widgets:
        lab_widgets.append({
            'labApp' : {
                'appUrl': widget['link'],
                'appTitle': widget['name'],
                'externalUrl': widget['external'],
            }
        })
    structure = {
            'id': create_lab_id(rlms, lab.laboratory_id, single),
            'title': lab.name,
            'description': lab.description or '',
            'domains' : { 'domain': domains },
            'ageRanges' : { 'ageRange': age_ranges },
            'labApps' : lab_widgets,
        }
    if lab.keywords:
        structure['keywords'] = { 'keyword': lab.keywords }
    else:
        structure['keywords'] = {}
    return structure


def app_to_xml(embed_app):
    age_ranges = embed_app.age_ranges # e.g., 12-13, 14-15
    domains = embed_app.domains # e.g., Physics, Chemistry
    lab_widgets = [{
        'labApp' : {
        'appUrl': url_for('embed.app_xml', identifier=embed_app.identifier, _external=True),
        'appTitle': embed_app.name,
        }
    }]
    return {
            'id':  create_app_id(embed_app),
            'title': embed_app.name,
            'description': embed_app.description or '',
            'domains' : { 'domain': domains},
            'ageRanges' : { 'ageRange': age_ranges },
            'labApps' : lab_widgets,
            'keywords' : {}
        }


def extract_labs(rlms, single_lab = None, fmt='json', age_ranges = None, domains = None):
    if fmt == 'xml':
        lab_formatter = lab_to_xml
    else:
        lab_formatter = lab_to_json
    RLMS_CLASS = get_manager_class(rlms.kind, rlms.version, rlms.id)
    rlms_inst = RLMS_CLASS(rlms.configuration)
    labs = rlms_inst.get_laboratories()
    public_laboratories = []
    for lab in labs:
        if single_lab is not None and lab.laboratory_id != single_lab:
            # If filtering, remove those labs
            continue

        if Capabilities.WIDGET in rlms_inst.get_capabilities():
            widgets = rlms_inst.list_widgets(lab.laboratory_id)
        else:
            widgets = [ { 'name' : lab.name, 'description' : lab.description } ]

        lab_widgets = []
        for widget in widgets:
            if single_lab is None:
                link = url_for('opensocial.public_rlms_widget_xml', rlms_identifier=rlms.public_identifier, lab_name=lab.laboratory_id, widget_name = widget['name'], _external=True)
                if link.startswith('https://'):
                    link = link.replace('https://', 'http://', 1)
                external_url = url_for('repository.preview_public_rlms', rlms_id=rlms.public_identifier, widget_name=widget['name'], lab_name=lab.laboratory_id, _external=True)
            else:
                link = url_for('opensocial.public_widget_xml', lab_name=lab.public_identifier, widget_name = widget['name'], _external=True)
                if link.startswith('https://'):
                    link = link.replace('https://', 'http://', 1)
                external_url = url_for('repository.preview_public_lab', widget_name=widget['name'], public_identifier=lab.public_identifier, _external=True)

            lab_widgets.append({
                'name': widget['name'],
                'description': widget['description'],
                'link': link,
                'external': external_url,
            })

        public_laboratories.append(lab_formatter(lab, lab_widgets, rlms, single_lab is not None, age_ranges, domains))
    return public_laboratories

def _get_resources(fmt = 'json'):
    if request.args.get('nocache', '') not in ('1','True', 'true'):
        force_cache()
    public_laboratories = []
    for lab in db.session.query(Laboratory).filter_by(publicly_available = True):
        for public_lab in extract_labs(rlms, lab.laboratory_id, fmt=fmt):
            public_laboratories.append(public_lab)
   
    for rlms in db.session.query(RLMS).filter_by(publicly_available = True):
        for public_lab in extract_labs(rlms, fmt=fmt):
            public_laboratories.append(public_lab)

    if False:
        # DO NOT ADD EMBEDDED APPS TO THE REPOSITORY
        if fmt == 'xml':
            app_formatter = app_to_xml
        else:
            app_formatter = app_to_json

        for app in db.session.query(EmbedApplication).all():
            public_laboratories.append(app_formatter(app))

    return public_laboratories

@repository_blueprint.route('/metadata.json')
def resources():
    public_laboratories = _get_resources(fmt='json')
    return jsonify(resources=public_laboratories)

@repository_blueprint.route('/metadata.xml')
def resources_xml():
    public_laboratories = _get_resources(fmt='xml')
    return Response(dict2xml({
        "resources": {
            "resource" : public_laboratories
        }
    }), mimetype='application/xml')

@repository_blueprint.route('/metadata.html')
def resources_html():
    fmt = request.args.get('format') or 'json'
    if fmt == 'xml':
        public_laboratories = _get_resources(fmt='xml')
        contents = dict2xml({
            "resources": {
                "resource" : public_laboratories
            }
        })
    else:
        contents = json.dumps(_get_resources(fmt='json'))
    return render_template_string("<html><body>Contents: <pre>{{ contents }}</pre></body></html>", contents=contents)

def _get_widgets(rlms, laboratory_id):
    if Capabilities.WIDGET in rlms.get_capabilities():
        return rlms.list_widgets(laboratory_id)

    return [ { 'name' : 'lab', 'description' : 'Main view of the laboratory' } ]

@repository_blueprint.route('/preview/rlms/<rlms_id>/<widget_name>/<everything:lab_name>')
def preview_public_rlms(rlms_id, widget_name, lab_name):
    db_rlms = db.session.query(RLMS).filter_by(publicly_available=True, public_identifier=rlms_id).first()
    if db_rlms is None:
        return "Laboratory not found", 404
    
    rlms = db_rlms.get_rlms()
    for lab in rlms.get_laboratories():
        if lab.laboratory_id == lab_name:
            widgets = _get_widgets(rlms, lab.laboratory_id)

            links = [] 
            for widget in widgets:
                if widget['name'] == widget_name:
                    reservation = rlms.reserve(lab.laboratory_id, 'anonymous', 'preview', '{}', [], {}, {}, locale=request.args.get('locale', 'en'))
                    return redirect(reservation['load_url'])
                    
    
    return "Laboratory not found", 404
    
@repository_blueprint.route('/preview/lab/<widget_name>/<everything:public_identifier>')
def preview_public_lab(widget_name, public_identifier):
    db_laboratory = db.session.query(Laboratory).filter_by(publicly_available=True, public_identifier=public_identifier).first()
    if db_laboratory is None:
        return "Laboratory not found", 404

    rlms = db_laboratory.rlms.get_rlms()
    for lab in rlms.get_laboratories():
        if lab.laboratory_id == db_laboratory.laboratory_id:
            widgets = _get_widgets(rlms, lab.laboratory_id)
            links = []
            for widget in widgets:
                if widget['name'] == widget_name:
                    reservation = rlms.reserve(lab.laboratory_id, 'anonymous', 'preview', '{}', [], {}, {}, locale=request.args.get('locale', 'en'))
                    return redirect(reservation['load_url'])

    return "Laboratory not found", 404

