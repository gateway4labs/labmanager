import json
from flask import Blueprint, jsonify, url_for, request, current_app, Response, render_template_string

from dict2xml import dict2xml

from labmanager.db import db
from labmanager.models import RLMS, Laboratory, EmbedApplication
from labmanager.rlms import get_manager_class, Capabilities

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

def lab_to_json(lab, widgets):
    age_ranges = lab.age_ranges or [] # e.g., 12-13, 14-15
    domains = lab.domains or [] # e.g., Physics, Chemistry
    lab_widgets = []
    for widget in widgets:
        lab_widgets.append({
            'app_url': widget['link'],
            'app_title': widget['name'],
        })
    return {
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
            'title': embed_app.name,
            'description': embed_app.description or '',
            'domains' : domains,
            'age_range' : age_ranges,
            'lab_apps' : lab_widgets,
            'keywords' : []
        }

def lab_to_xml(lab, widgets):
    age_ranges = lab.age_ranges or [] # e.g., 12-13, 14-15
    domains = lab.domains or [] # e.g., Physics, Chemistry
    lab_widgets = []
    for widget in widgets:
        lab_widgets.append({
            'labApp' : {
                'appUrl': widget['link'],
                'appTitle': widget['name'],
            }
        })
    structure = {
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
            'title': embed_app.name,
            'description': embed_app.description or '',
            'domains' : { 'domain': domains},
            'ageRanges' : { 'ageRange': age_ranges },
            'labApps' : lab_widgets,
            'keywords' : {}
        }


def _extract_labs(rlms, single_lab = None, fmt='json'):
    if fmt == 'xml':
        lab_formatter = lab_to_xml
    else:
        lab_formatter = lab_to_json
    RLMS_CLASS = get_manager_class(rlms.kind, rlms.version, rlms.id)
    rlms_inst = RLMS_CLASS(rlms.configuration)
    labs = rlms_inst.get_laboratories()
    public_laboratories = []
    for lab in labs:
        if single_lab is not None and lab.laboratory_id != single_lab.laboratory_id:
            # If filtering, remove those labs
            continue

        if Capabilities.WIDGET in rlms_inst.get_capabilities():
            widgets = rlms_inst.list_widgets(lab.laboratory_id)
        else:
            widgets = [ { 'name' : lab.name, 'description' : lab.description } ]

        lab_widgets = []
        for widget in widgets:
            link = url_for('opensocial.public_rlms_widget_xml', rlms_identifier=rlms.public_identifier, lab_name=lab.laboratory_id, widget_name = widget['name'], _external=True)
            lab_widgets.append({
                'name': widget['name'],
                'description': widget['description'],
                'link': link,
            })

        public_laboratories.append(lab_formatter(lab, lab_widgets))
    return public_laboratories

def _get_resources(fmt = 'json'):
    public_laboratories = []
    for lab in db.session.query(Laboratory).filter_by(publicly_available = True):
        for public_lab in _extract_labs(rlms, lab, fmt=fmt):
            public_laboratories.append(public_lab)
   
    for rlms in db.session.query(RLMS).filter_by(publicly_available = True):
        for public_lab in _extract_labs(rlms, fmt=fmt):
            public_laboratories.append(public_lab)

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


