import json
import urllib2
import threading

from flask import Blueprint, request, redirect, render_template

from labmanager.db import db_session
from labmanager.models import LMS, PermissionToLms
from labmanager.rlms import get_manager_class

SHINDIG = threading.local()

def url_shindig(url):
    if SHINDIG.url.endswith('/'):
        base_url = SHINDIG.url[:len(SHINDIG.url) - 1]
    else:
        base_url = SHINDIG.url
    return '%s%s' % (base_url, url)

def get_parent_spaces(space_id, spaces):
    try:
        json_contents = urllib2.urlopen(url_shindig('/rest/spaces/%s' % space_id)).read()
        contents = json.loads(json_contents)
    except:
        # Invalid permission or whatever
        return

    parent_type = contents['entry'].get('parentType','')
    if parent_type != '@space':
        return

    parent_id = contents['entry'].get('parentId', '')
    if parent_id not in spaces:
        spaces.append(parent_id)
        get_parent_spaces(parent_id, spaces)


opensocial_blueprint = Blueprint('opensocial', __name__)

@opensocial_blueprint.route("/widgets/<institution_id>/<lab_name>/widget_<widget_name>.xml")
def widget_xml(institution_id, lab_name, widget_name):
    return render_template('/opensocial/widget.xml', institution_id = institution_id, lab_name = lab_name, widget_name = widget_name)


@opensocial_blueprint.route("/reservations/new/<institution_id>/<lab_name>/")
def reserve(institution_id, lab_name):
    st = request.args.get('st') or ''

    institution = db_session.query(LMS).filter_by(name = institution_id).first()
    if institution is None or len(institution.shindig_credentials) < 1:
        return "This is not a valid PLE. Make sure that the institution id is fine and that there are Shindig Credentials configured"

    SHINDIG.url = institution.shindig_credentials[0].shindig_url

    # Obtain user data
    current_user_str  = urllib2.urlopen(url_shindig("/rest/people/@me/@self?st=%s" % st)).read()
    current_user_data = json.loads(current_user_str)

    # name    = current_user_data['entry'].get('displayName') or 'anonymous'
    user_id = current_user_data['entry'].get('id') or 'no-id'

    # Obtain current application data (especially, on which space is the user running it)
    current_app_str  = urllib2.urlopen(url_shindig('/rest/apps/@self?st=%s' % st)).read()
    current_app_data = json.loads(current_app_str)

    space_id = current_app_data['entry'].get('parentId') or 'null parent'
    parent_type = current_app_data['entry'].get('parentType')
    if parent_type != '@space':
        return render_template("opensocial/errors.html", message =  "Invalid parent: it should be a space, and it is a %s" % parent_type)

    # Obtain the list of parent spaces of that space
    spaces = [space_id]
    get_parent_spaces(space_id, spaces)

    # Now: check for that institution if there is a permission identified by that lab_name,
    # and check which courses (spaces in OpenSocial) have that permission.

    permission = db_session.query(PermissionToLms).filter_by(lms = institution, local_identifier = lab_name).first()
    if permission is None:
        return render_template("opensocial/errors.html", message = "Your PLE is valid, but don't have permissions for the requested laboratory.")

    courses_configurations = []
    for course_permission in permission.course_permissions:
        if course_permission.course.context_id in spaces:
            # Let the server choose among the best possible configuration
            courses_configurations.append(course_permission.configuration)

    if len(courses_configurations) == 0:
        return render_template("opensocial/errors.html", message = "Your PLE is valid and your lab too, but you're not in one of the spaces that have permissions (you are in %r)" % spaces)

    ple_configuration = permission.configuration
    db_laboratory     = permission.laboratory
    db_rlms           = db_laboratory.rlms
    rlms_version      = db_rlms.version
    rlms_kind         = db_rlms.kind

    request_payload = {} # This could be populated in the HTML. Pending.
    user_agent = unicode(request.user_agent)
    origin_ip  = request.remote_addr
    referer    = request.referrer

    # 
    # Load the plug-in for the current RLMS, and instanciate it
    ManagerClass = get_manager_class(rlms_kind, rlms_version)
    remote_laboratory = ManagerClass(db_rlms.configuration)
    
    response = remote_laboratory.reserve(laboratory_id             = db_laboratory.laboratory_id,
                                                username                  = user_id,
                                                general_configuration_str = ple_configuration,
                                                particular_configurations = courses_configurations,
                                                request_payload           = request_payload,
                                                user_properties           = {
                                                    'user_agent' : user_agent,
                                                    'from_ip'    : origin_ip,
                                                    'referer'    : referer
                                                })
    return render_template("opensocial/confirmed.html", reservation_id = response['reservation_id'], shindig_url = SHINDIG.url)


@opensocial_blueprint.route("/reservations/existing/<institution_id>/<lab_name>/<widget_name>/")
def open_widget(institution_id, lab_name, widget_name):
    reservation_id = request.args.get('reservation-id') or ''

    institution = db_session.query(LMS).filter_by(name = institution_id).first()
    if institution is None or len(institution.shindig_credentials) == 0:
        return "Institution not found or it does not support Shindig"

    permission = db_session.query(PermissionToLms).filter_by(lms = institution, local_identifier = lab_name).first()
    db_laboratory     = permission.laboratory
    db_rlms           = db_laboratory.rlms
    rlms_version      = db_rlms.version
    rlms_kind         = db_rlms.kind

    ManagerClass = get_manager_class(rlms_kind, rlms_version)
    remote_laboratory = ManagerClass(db_rlms.configuration)

    response = remote_laboratory.load_widget(reservation_id, widget_name)
    widget_contents_url = response['url']
    return redirect(widget_contents_url)

@opensocial_blueprint.route("/smartgateway/<institution_id>/<lab_name>/sg.js")
def smartgateway(institution_id, lab_name):
    return render_template("opensocial/smartgateway.js", institution_id = institution_id, lab_name = lab_name)


