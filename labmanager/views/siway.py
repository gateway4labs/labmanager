from flask import Blueprint, jsonify, url_for

from labmanager.db import db
from labmanager.models import RLMS, Laboratory
from labmanager.rlms import get_manager_class, Capabilities

siway_blueprint = Blueprint('siway', __name__)

@siway_blueprint.route('/')
def index():
    return "Welcome to SiWay"

def lab_to_json(lab, link):
    age_ranges = [] # e.g., 12-13, 14-15
    age_ranges = ['12-14', '14-16', '>18'] 
    domains = ['physics', 'chemistry'] # e.g., Physics, Chemistry
    return {
            'title': lab.name,
            'description': "This is a sample resource",
            'domains' : domains,
            'age_range' : age_ranges,
            'lab_apps' : [
                {
					'app_url': link,
					'app_title': lab.name,
				}
            ],
        }

@siway_blueprint.route('/metadata.json')
def resources():
    public_laboratories = []
    for lab in db.session.query(Laboratory).filter_by(publicly_available = True):
        # TODO: default
        link = url_for('opensocial.public_widget_xml', lab_name = lab.public_identifier, widget_name = 'default', _external=True)
        public_laboratories.append(lab_to_json(lab, link))
    
    for rlms in db.session.query(RLMS).filter_by(publicly_available = True):
        # TODO: use this
        RLMS_CLASS = get_manager_class(rlms.kind, rlms.version, rlms.id)
        rlms_inst = RLMS_CLASS(rlms.configuration)
        labs = rlms_inst.get_laboratories()
        for lab in labs:
            if Capabilities.WIDGET in rlms_inst.get_capabilities():
                widgets = rlms_inst.list_widgets(lab.laboratory_id)
            else:
                widgets = [ { 'name' : 'lab', 'description' : 'Main view of the laboratory' } ]

        for lab in rlms.laboratories:
            # TODO: use the other approach (above)
            link = url_for('opensocial.public_rlms_widget_xml', rlms_identifier=rlms.public_identifier, lab_name='example', widget_name = 'default', _external=True)
            public_laboratories.append(lab_to_json(lab, link))

    return jsonify(resources=public_laboratories)
