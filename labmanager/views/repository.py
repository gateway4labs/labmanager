from flask import Blueprint, jsonify, url_for, request, current_app, Response

from labmanager.db import db
from labmanager.models import RLMS, Laboratory
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
    age_ranges = [] # e.g., 12-13, 14-15
    age_ranges = lab.age_ranges or []
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

def _extract_labs(rlms, single_lab = None):
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

        public_laboratories.append(lab_to_json(lab, lab_widgets))
    return public_laboratories

@repository_blueprint.route('/metadata.json')
def resources():
    public_laboratories = []
    for lab in db.session.query(Laboratory).filter_by(publicly_available = True):
        for public_lab in _extract_labs(rlms, lab):
            public_laboratories.append(public_lab)
   
    for rlms in db.session.query(RLMS).filter_by(publicly_available = True):
        for public_lab in _extract_labs(rlms):
            public_laboratories.append(public_lab)

    return jsonify(resources=public_laboratories)
