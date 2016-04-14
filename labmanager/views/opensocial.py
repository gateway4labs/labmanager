import time
import json
import random
import urllib
import urllib2
import hashlib
import urlparse
import datetime
import traceback
import threading


from functools import wraps
import xml.etree.ElementTree as ET

import requests

from flask import Blueprint, request, redirect, render_template, url_for, Response, make_response, jsonify
from flask.ext.wtf import Form, validators, TextField, PasswordField
from labmanager.db import db
from labmanager.models import LearningTool, PermissionToLt, LtUser, ShindigCredentials, Laboratory, RLMS
from labmanager.rlms import get_manager_class, Capabilities
import labmanager.forms as forms
from labmanager.babel import gettext, lazy_gettext
from labmanager.utils import remote_addr
from labmanager.views.translations import DEFAULT_TRANSLATIONS
from labmanager import app

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

def _extract_widget_config(rlms_db, laboratory_identifier, widget_name, lab_found):
    autoload = None
    if request.args.get('autoload'):
        autoload = request.args['autoload'].lower() == 'true'

    height = None
    if request.args.get('height'):
        try:
            height = '%spx' % int(request.args['height'])
        except:
            pass
    
    base_data = {
        'translations' : {},
        'mails' : {}
    }
    if height is not None:
        base_data['height'] = height

    scale = None
    if request.args.get('scale'):
        try:
            scale = int(request.args['scale'])
        except:
            pass

    if scale is not None:
        base_data['scale'] = scale

    if not lab_found:
        return base_data

    if autoload is None and rlms_db.default_autoload is not None:
        autoload = rlms_db.default_autoload

    RLMS_CLASS = get_manager_class(rlms_db.kind, rlms_db.version, rlms_db.id)
    rlms = RLMS_CLASS(rlms_db.configuration)

    try:
        capabilities = rlms.get_capabilities()
    except Exception as e:
        traceback.print_exc()
        raise Exception("Error retrieving capabilities: %s" % e)

    if Capabilities.FORCE_SEARCH in capabilities:
        if autoload is None:
            autoload = True # By default in those cases where a search is mandatory
    else:
        # labs = [ lab for lab in rlms.get_laboratories() if lab.laboratory_id == laboratory_identifier ]
        # if not labs:
        #     # The laboratory has changed
        #     return None
        # 
        # if autoload is None:
        #     autoload = labs[0].autoload
        pass
    
    if Capabilities.TRANSLATIONS in capabilities:
        translations = rlms.get_translations(laboratory_identifier)
        if 'translations' not in translations:
            translations['translations'] = {}
        if 'mails' not in translations:
            translations['mails'] = []
    else:
        translations = {'translations' : {}, 'mails' : []}

    # Only if no translation is regularly provided and translation_list is supoprted
    if len(translations['translations']) == 0 and Capabilities.TRANSLATION_LIST in capabilities:
        translation_list = list((rlms.get_translation_list(laboratory_identifier) or {}).get('supported_languages', []))
    else:
        translation_list = []

    if autoload and len(translations['translations']) == 0:
        show_languages = False
    else:
        show_languages = True
        
    show_empty_languages = len(translation_list) > 0

    if Capabilities.WIDGET in capabilities:
        widgets = rlms.list_widgets(laboratory_identifier)

        for widget in widgets:
            if widget['name'] == widget_name:
                widget['autoload'] = autoload
                widget['translations'] = translations
                widget['translation_list'] = translation_list
                widget['show_languages'] = show_languages
                widget['show_empty_languages'] = show_empty_languages

                if height is not None:
                    widget['height'] = height

                if scale is not None:
                    widget['scale'] = scale

                return widget

    base_data['autoload'] = autoload
    base_data['translations'] = translations
    base_data['translation_list'] = translation_list
    base_data['show_languages'] = show_languages
    base_data['show_empty_languages'] = show_empty_languages
    return base_data

def xml_error_management(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            app.logger.error("Error processing request: %s" % e, exc_info = True)
            contents = render_template('opensocial/widget-error.xml', message="Error loading widget: %s" % e)
            return Response(contents, mimetype="application/xml")

    return wrapper

@opensocial_blueprint.route("/widgets/<institution_id>/<lab_name>/widget_<widget_name>.xml")
@opensocial_blueprint.route("/w/<institution_id>/<lab_name>/w_<widget_name>.xml")
@xml_error_management
def widget_xml(institution_id, lab_name, widget_name):
    public_lab = db.session.query(Laboratory).filter_by(public_identifier = lab_name, publicly_available = True).first()
    laboratory = public_lab
    if public_lab:
        widget_config = _extract_widget_config(public_lab.rlms, public_lab.laboratory_id, widget_name, True) 
    else:
        widget_config = {} # Default value
        institution = db.session.query(LearningTool).filter_by(name = institution_id).first()
        if institution:
            permission = db.session.query(PermissionToLt).filter_by(lt = institution, local_identifier = lab_name).first()
            if permission:
                widget_config = _extract_widget_config(permission.laboratory.rlms, permission.laboratory.laboratory_id, widget_name, False)
                laboratory = permission.laboratory 

    if widget_config is None:
        return "Error: widget does not exist anymore" # TODO
    if not laboratory:
        contents = render_template('opensocial/widget-error.xml',message="Lab %s not found or not public" % lab_name)
        return Response(contents, mimetype="application/xml")
    contents = render_template('/opensocial/widget.xml', institution_id = institution_id, lab_name = lab_name, widget_name = widget_name, widget_config = widget_config, autoload = widget_config['autoload'], rlms = public_lab.rlms, go_lab_booking = laboratory.go_lab_reservation)
    return Response(contents, mimetype="application/xml")

@opensocial_blueprint.route("/public/widgets/<lab_name>/widget_<widget_name>.xml",methods=[ 'GET'])
@opensocial_blueprint.route("/pub/<lab_name>/w_<widget_name>.xml",methods=[ 'GET'])
@xml_error_management
def public_widget_xml(lab_name, widget_name):
    laboratory = db.session.query(Laboratory).filter_by(public_identifier = lab_name, publicly_available = True).first()
    if not laboratory:
        contents = render_template('opensocial/widget-error.xml',message="Lab %s not found or not public" % lab_name)
        return Response(contents, mimetype="application/xml")
    widget_config = _extract_widget_config(laboratory.rlms, laboratory.laboratory_id, widget_name, True)     
    if widget_config is None:
        return "Error: widget does not exist anymore" # TODO  

    contents = render_template('/opensocial/widget.xml', public_lab = True, lab_name = lab_name, widget_name = widget_name, widget_config = widget_config, autoload = widget_config['autoload'], rlms = laboratory.rlms, go_lab_booking = laboratory.go_lab_reservation)
    return Response(contents, mimetype="application/xml")


@opensocial_blueprint.route("/pub/<rlms_identifier>/<quoted_url:lab_name>/w_<widget_name>.xml",methods=[ 'GET'])
@xml_error_management
def public_rlms_widget_xml(rlms_identifier, lab_name, widget_name):
    rlms = db.session.query(RLMS).filter_by(public_identifier = rlms_identifier, publicly_available = True).first()
    if not rlms:
        contents = render_template('opensocial/widget-error.xml',message="RLMS %s not found or not public" % rlms_identifier)
        return Response(contents, mimetype="application/xml")

    widget_config = _extract_widget_config(rlms, lab_name, widget_name, True)
    if widget_config is None:
        return "Error: widget does not exist anymore" # TODO  

#   XXX We do not support booking on the public labs yet
    print widget_config
    contents = render_template('/opensocial/widget.xml', rlms_identifier = rlms_identifier, public_rlms = True, lab_name = lab_name, widget_name = widget_name, widget_config = widget_config, autoload = widget_config['autoload'], rlms = rlms, go_lab_booking = False, go_lab_booking_url = "")
    return Response(contents, mimetype="application/xml")

def booking_system(laboratory):
    if laboratory.go_lab_reservation:
        token = request.args.get('token')
        url = 'https://www.weblab.deusto.es/golab/booking/verify/verify_token?token=%s' % token
        try:
            r =requests.get(url)
            response = r.json()
            if not response:
                return False
        except Exception as e:
            raise ValueError('Error in request with url',url)
    return True

def _indent(elem, level=0):
    i = "\n" + level*"  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            _indent(elem, level+1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i

def _translations_to_xml(translations_response, language):
    xml_bundle = ET.Element("messagebundle")
    xml_bundle.attrib['automatic'] = "false"

    translations = translations_response.get('translations', {})
    mails = translations_response.get('mails', [])
    language = translations.get(language, {})
    if mails:
        xml_bundle.attrib['mails'] = ','.join(mails)

    for key, pack in language.iteritems():
        if 'value' not in pack:
            continue

        value = pack.get('value', '')
        namespace = pack.get('namespace')
        category = pack.get('category')

        xml_msg = ET.SubElement(xml_bundle, 'msg')
        xml_msg.attrib['name'] = key

        if namespace:
            xml_msg.attrib['namespace'] = namespace

        if category:
            xml_msg.attrib['category'] = category
        
        if not isinstance(value, unicode):
            value = value.decode('utf-8')
        xml_msg.text = value
    _indent(xml_bundle)
    xml_string = ET.tostring(xml_bundle, encoding = 'UTF-8')
    return xml_string

def _rlms_to_translations(rlms_db, laboratory_id, language):
    translations = {}
    if rlms_db is not None:
        RLMS_CLASS = get_manager_class(rlms_db.kind, rlms_db.version, rlms_db.id)
        rlms = RLMS_CLASS(rlms_db.configuration)
        capabilities = rlms.get_capabilities()
        if Capabilities.TRANSLATIONS in capabilities:
            translations = rlms.get_translations(laboratory_id)

    if 'translations' not in translations:
        translations['translations'] = {}

    for lang in DEFAULT_TRANSLATIONS:
        if lang not in translations['translations']:
            translations['translations'][lang] = {}
        translations['translations'][lang].update(DEFAULT_TRANSLATIONS[lang])
    
    translations_xml = _translations_to_xml(translations, language)
    return Response(translations_xml, mimetype='application/xml')

@opensocial_blueprint.route("/w/<institution_id>/<lab_name>/languages/<lang>_ALL.xml")
def translations(institution_id, lab_name, lang):
    public_lab = db.session.query(Laboratory).filter_by(public_identifier = lab_name, publicly_available = True).first()
    laboratory = public_lab
    if not public_lab:
        institution = db.session.query(LearningTool).filter_by(name = institution_id).first()
        if institution:
            permission = db.session.query(PermissionToLt).filter_by(lt = institution, local_identifier = lab_name).first()
            if permission:
                laboratory = permission.laboratory

    if not laboratory:
        return _rlms_to_translations(None, None, lang)

    return _rlms_to_translations(laboratory.rlms, laboratory.laboratory_id, lang)

@opensocial_blueprint.route("/pub/<lab_name>/languages/<lang>_ALL.xml")
def public_translations(lab_name, lang):
    laboratory = db.session.query(Laboratory).filter_by(public_identifier = lab_name, publicly_available = True).first()
    if not laboratory:
        return _rlms_to_translations(None, None, lang)
    
    return _rlms_to_translations(laboratory.rlms, laboratory.laboratory_id, lang)

@opensocial_blueprint.route("/pub/<rlms_identifier>/<quoted_url:lab_name>/languages/<lang>_ALL.xml")
def public_rlms_translations(rlms_identifier, lab_name, lang):
    rlms = db.session.query(RLMS).filter_by(public_identifier = rlms_identifier, publicly_available = True).first()
    if not rlms:
        return _rlms_to_translations(None, None, lang)

    return _rlms_to_translations(rlms, lab_name, lang)

@opensocial_blueprint.route("/reload")
def reload():
    return render_template("opensocial/reload.html")


INVALID_WIDGET_NAME = 'THIS_IS_NOT_A_VALID_WIDGET_NAME'

@opensocial_blueprint.route("/reservations/new/<institution_id>/<lab_name>/")
def reserve(institution_id, lab_name):
    gadget_url_base = url_for('.widget_xml', institution_name = institution_id, lab_name = lab_name, widget_name = INVALID_WIDGET_NAME, _external = True).rsplit(INVALID_WIDGET_NAME, 1)[0]
    return _reserve_impl(lab_name, institution_id = institution_id, gadget_url_base = gadget_url_base)

@opensocial_blueprint.route("/public/reservations/new/<lab_name>/")
def public_reserve(lab_name):
    gadget_url_base = url_for('.public_widget_xml', lab_name = lab_name, widget_name = INVALID_WIDGET_NAME, _external = True).rsplit(INVALID_WIDGET_NAME, 1)[0]
    return _reserve_impl(lab_name, public_lab = True, gadget_url_base = gadget_url_base)

@opensocial_blueprint.route("/public/reservations/new/<rlms_identifier>/<quoted_url:lab_name>/")
def public_rlms_reserve(rlms_identifier, lab_name):
    gadget_url_base = url_for('.public_rlms_widget_xml', rlms_identifier = rlms_identifier, lab_name = lab_name, widget_name = INVALID_WIDGET_NAME, _external = True).rsplit(INVALID_WIDGET_NAME, 1)[0]
    return _reserve_impl(lab_name, public_rlms = True, rlms_identifier = rlms_identifier, gadget_url_base = None)

def _reserve_impl(lab_name, public_rlms = False, public_lab = False, institution_id = None, rlms_identifier = None, gadget_url_base = None):
    # TODO XXX SECURITY BUG: THIS METHOD DOES NOT USE THE BOOKING THING
    st = request.args.get('st') or ''
    SHINDIG.url = 'http://shindig2.epfl.ch'

    if public_rlms:
        db_rlms = db.session.query(RLMS).filter_by(publicly_available = True, public_identifier = rlms_identifier).first()
        if db_rlms is None:
            return render_template("opensocial/errors.html", message = gettext("That lab does not exist or it is not publicly available."))
        lab_identifier = lab_name

        ple_configuration = '{}'
        institution_name  = 'public-labs' # TODO: make sure that this name is unique
        courses_configurations = []
        booking_required = False
    else:
        if public_lab:
            db_laboratory = db.session.query(Laboratory).filter_by(publicly_available = True, public_identifier = lab_name).first()
            if db_laboratory is None:
                return render_template("opensocial/errors.html", message = gettext("That lab does not exist or it is not publicly available."))
            
            ple_configuration = '{}'
            institution_name  = 'public-labs' # TODO: make sure that this name is unique
            courses_configurations = []
        else:
            institution = db.session.query(LearningTool).filter_by(name = institution_id).first()
            if institution is None or len(institution.shindig_credentials) < 1:
                return render_template("opensocial/errors.html", message = gettext("This is not a valid PLE. Make sure that the institution id is fine and that there are Shindig Credentials configured"))

            SHINDIG.url = institution.shindig_credentials[0].shindig_url

            # Obtain current application data (especially, on which space is the user running it)
            current_app_str  = urllib2.urlopen(url_shindig('/rest/apps/@self?st=%s' % st)).read()
            current_app_data = json.loads(current_app_str)
            space_id = current_app_data['entry'].get('parentId') or 'null parent'
            parent_type = current_app_data['entry'].get('parentType')
            if parent_type != '@space':
                return render_template("opensocial/errors.html", message = gettext("Invalid parent: it should be a space, and it is a %(parenttype)s", parenttype=parent_type))
            # Obtain the list of parent spaces of that space
            spaces = [space_id]
            get_parent_spaces(space_id, spaces)
            # Now, check permissions:
            # First, check if the lab is public (e.g. the lab can be accessed by anyone)
            # Second, check accesibility permissions (e.g. the lab is accessible for everyone from that institution without specifying any Graasp space). 
            # After that, in the case that there are not accesibility permissions, check for that institution if there is a permission identified by that lab_name, and check which courses (spaces in OpenSocial) have that permission.
            public_lab_db = db.session.query(Laboratory).filter_by(public_identifier = lab_name, publicly_available = True).first()
            courses_configurations = []
            if public_lab_db is None:
                # No public access is granted for the lab, check accesibility permissions
                accessible_permission = db.session.query(PermissionToLt).filter_by(lt = institution, local_identifier = lab_name, accessible = True).first()
                if accessible_permission is None:
                    permission = db.session.query(PermissionToLt).filter_by(lt = institution, local_identifier = lab_name).first()
                    if permission is None:
                        return render_template("opensocial/errors.html", message = gettext("Your PLE is valid, but don't have permissions for the requested laboratory."))
                    for course_permission in permission.course_permissions:
                        if course_permission.course.context_id in spaces:
                            # Let the server choose among the best possible configuration
                            courses_configurations.append(course_permission.configuration)
                    if len(courses_configurations) == 0:
                        return render_template("opensocial/errors.html", message = gettext("Your PLE is valid and your lab too, but you're not in one of the spaces that have permissions (you are in %(space)r)", space=spaces))
                else:
                    # There is a accesibility permission for that lab and institution
                    permission = accessible_permission

                ple_configuration = permission.configuration
                db_laboratory     = permission.laboratory
                institution_name  = institution.name
            else: 
                # There is a public permission for the lab
                ple_configuration = []
                db_laboratory     = public_lab_db
                institution_name  = institution.name

        booking_required = db_laboratory.go_lab_reservation
        lab_identifier = db_laboratory.laboratory_id
        db_rlms = db_laboratory.rlms

    if booking_required:
        next_session = check_ils_booking(gadget_url_base)
        if next_session is not None:
            return render_template("opensocial/errors-booking.html", next_session = next_session)

    # Obtain user data
    if st == 'null' and (public_lab or public_rlms):
        user_id = 'no-id'
    else:
        try:
            current_user_str  = urllib2.urlopen(url_shindig("/rest/people/@me/@self?st=%s" % st)).read()
            current_user_data = json.loads(current_user_str)
        except:
            traceback.print_exc()
            if public_lab or public_rlms:
                user_id = 'no-id'
            else:
                return render_template("opensocial/errors.html", message = gettext("Could not connect to %(urlshindig)s.", urlshindig=url_shindig("/rest/people/@me/@self?st=%s" % st)))
        else:
            # name    = current_user_data['entry'].get('displayName') or 'anonymous'
            user_id = current_user_data['entry'].get('id') or 'no-id'

    rlms_version      = db_rlms.version
    rlms_kind         = db_rlms.kind
    user_agent = unicode(request.user_agent)
    origin_ip  = remote_addr()
    referer    = request.referrer
    # Load the plug-in for the current RLMS, and instanciate it
    ManagerClass = get_manager_class(rlms_kind, rlms_version, db_rlms.id)
    remote_laboratory = ManagerClass(db_rlms.configuration)

    kwargs = {}

    locale = request.args.get('locale') or None
    if locale:
        kwargs['locale'] = locale

    lab_config = request.args.get('lab_config')
    try:
        lab_config = urllib.unquote(lab_config)
        json.loads(lab_config) # Verify that it's a valid JSON
    except:
        lab_config = '{}'
    if lab_config:
        request_payload = { 'initial' : lab_config }
    else:
        request_payload = {}

    try:
        response = remote_laboratory.reserve(laboratory_id                = lab_identifier,
                                                username                  = user_id,
                                                institution               = institution_name,
                                                general_configuration_str = ple_configuration,
                                                particular_configurations = courses_configurations,
                                                request_payload           = request_payload,
                                                user_properties           = {
                                                    'user_agent' : user_agent,
                                                    'from_ip'    : origin_ip,
                                                    'referer'    : referer
                                                },
                                                back = url_for('.reload', _external = True),
                                                **kwargs)
    except Exception as e:
        app.logger.error("Error processing request: %s" % e, exc_info = True)
        traceback.print_exc()
        # Don't translate, just in case there are issues with the problem itself
        return render_template("opensocial/errors.html", message = "There was an error performing the reservation to the final laboratory.")
    else:
        if Capabilities.WIDGET in remote_laboratory.get_capabilities():
            reservation_id = response['reservation_id']
        else:
            reservation_id = response['load_url']

        quoted_reservation_id = urllib2.quote(reservation_id, '')
        g4l_session_id = "{0}-{1}-{2}".format(quoted_reservation_id, time.time(), str(random.randint(0, 9999)).zfill(4))

        return render_template("opensocial/confirmed.html", reservation_id = quoted_reservation_id, g4l_session_id = g4l_session_id, shindig_url = SHINDIG.url)

def extract_ils_id(url):
    if url is None:
        return None

    try:
        path = urlparse.urlparse(url).path
        identifier = path.split('/')[2]
    except Exception:
        traceback.print_exc()
        return None
    else:
        return identifier

def _check_lab_booking_response(gadget_url_base):
    next_session = check_ils_booking(gadget_url_base)
    if next_session is not None:
        next_session = next_session.strftime('%Y-%m-%dT%H:%M:%S')

    serialized_response = json.dumps(dict(error = False, next_session = next_session, booked = next_session is not None))
    return Response(serialized_response, headers = {
        'Access-Control-Allow-Origin': '*'
    }, content_type = 'application/json')

@opensocial_blueprint.route("/booking/<institution_id>/<lab_name>/")
def check_laboratory_booking(institution_id, lab_name):
    gadget_url_base = url_for('.widget_xml', institution_name = institution_id, lab_name = lab_name, widget_name = INVALID_WIDGET_NAME, _external = True).rsplit(INVALID_WIDGET_NAME, 1)[0]
    return _check_lab_booking_response(gadget_url_base)

@opensocial_blueprint.route("/public/booking/<lab_name>/")
def check_public_laboratory_booking(lab_name):
    gadget_url_base = url_for('.public_widget_xml', lab_name = lab_name, widget_name = INVALID_WIDGET_NAME, _external = True).rsplit(INVALID_WIDGET_NAME, 1)[0]
    return _check_lab_booking_response(gadget_url_base)

def check_ils_booking(gadget_url_base):
    """
    Checks the session and returns when the lab is free (in UTC). If None is returned, it means that there is no ongoing session so they can use the lab.
    """
    ils_student_id = extract_ils_id(request.args.get('ils_student_url'))
    ils_teacher_id = extract_ils_id(request.args.get('ils_teacher_url'))

    # BOOKING_URL = url_for('.mock_golabz_booking_service', _external=True)
    BOOKING_URL = 'http://www.golabz.eu/rest/lab-booking/retrieve.json'

    try:
        r = requests.get(BOOKING_URL, headers = {
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
        })
        r.raise_for_status()
        booking_slots = r.json()
    except Exception as e:
        traceback.print_exc()
        # We can not stop students using the labs if the service is temporarily down
        return None

    affected_ilss = []
    oldest_affected_endtime = datetime.datetime.utcnow()
    for booking_slot in booking_slots:
        is_current_lab = False
        for lab_app in booking_slot.get('lab_apps', []):
            lab_url = lab_app.get('app_url', '')
            if lab_url.startswith(gadget_url_base):
                is_current_lab = True
                break

        if not is_current_lab:
            continue
        
        start_time_str = booking_slot.get('start_time', '2000-01-01T00:00:00')
        end_time_str = booking_slot.get('end_time', '2000-01-01T00:00:00')
        FORMAT = '%Y-%m-%dT%H:%M:%S'

        try:
            start_time = datetime.datetime.strptime(start_time_str, FORMAT)
            end_time = datetime.datetime.strptime(end_time_str, FORMAT)
        except ValueError:
            traceback.print_exc()
            continue

        now = datetime.datetime.utcnow()
        if end_time > now > start_time:
            ils_id = extract_ils_id(booking_slot.get('ils_url')) or 'does.not.exist'
            if end_time > oldest_affected_endtime:
                oldest_affected_endtime = end_time
            affected_ilss.append(ils_id)

    if affected_ilss:
        for affected_ils_id in affected_ilss:
            if affected_ils_id in (ils_student_id, ils_teacher_id):
                return None
        # If there are affected ILS, but we're not part of them, we're not authorized
        return oldest_affected_endtime
    else:
        # If there is no affected ILS, it doesn't matter if we're in the group or not
        return None


@opensocial_blueprint.route("/mock_golabz_booking_service.json")
def mock_golabz_booking_service():
    response = [
        {
            "title":"Luminescent Labs",
            "id":"155",
            "ils_url":"http://graasp.eu/ils/55f605fd06a9ab76eb10e3db/?lang=en",
            "lab_apps": [
                {
                    'app_url' : "http://localhost/foobar/",
                    'app_type' : 'Open Social widget',
                },
                {
                    'app_url' : "http://localhost:5000/os/pub/acidbase/w_default.xml",
                    'app_type' : 'Open Social widget',
                },
                {
                    'app_url' : "http://gateway.golabz.eu/os/pub/travoltage-booking/w_default.xml",
                    'app_type': 'Open Social widget',
                }
            ],
            "user_id":"10",
            "user_mail":"yiwei.cao@gmail.com",
            "start_time":"2010-09-30T14:30:00",
            "end_time":"2030-09-30T15:30:00"
        }
    ]
    r = make_response(json.dumps(response))
    r.content_type = 'application/json'
    return r

@opensocial_blueprint.route("/reservations/existing/<institution_id>/<lab_name>/<widget_name>/")
def open_widget(institution_id, lab_name, widget_name):
    return _open_widget_impl(lab_name, widget_name, institution_id = institution_id)

@opensocial_blueprint.route("/public/reservations/existing/<lab_name>/<widget_name>/")
def open_public_widget(lab_name, widget_name):
    return _open_widget_impl(lab_name, widget_name, public_lab = True)

@opensocial_blueprint.route("/public/reservations/existing/<rlms_identifier>/<quoted_url:lab_name>/<widget_name>/")
def open_public_rlms_widget(rlms_identifier, lab_name, widget_name):
    return _open_widget_impl(lab_name, widget_name, public_rlms = True, rlms_identifier = rlms_identifier)

@xml_error_management
def _open_widget_impl(lab_name, widget_name, public_lab = False, public_rlms = False, institution_id = None, rlms_identifier = None):
    if public_rlms:
        db_rlms = db.session.query(RLMS).filter_by(publicly_available = True, public_identifier = rlms_identifier).first()
        if db_rlms is None:
            return gettext("RLMS not found")
    else:
        if public_lab:
            db_laboratory = db.session.query(Laboratory).filter_by(publicly_available = True, public_identifier = lab_name).first()
        else:
            institution = db.session.query(LearningTool).filter_by(name = institution_id).first()
            if institution is None or len(institution.shindig_credentials) == 0:
                return gettext("Institution not found or it does not support Shindig")
            permission = db.session.query(PermissionToLt).filter_by(lt = institution, local_identifier = lab_name).first()
            db_laboratory     = permission.laboratory if permission is not None else None

        if db_laboratory is None:
            return gettext("Laboratory not found")

        db_rlms           = db_laboratory.rlms

    rlms_version      = db_rlms.version
    rlms_kind         = db_rlms.kind
    ManagerClass = get_manager_class(rlms_kind, rlms_version, db_rlms.id)
    remote_laboratory = ManagerClass(db_rlms.configuration)
    reservation_id = request.args.get('reservation_id') or 'reservation-id-not-found'
    locale = request.args.get('locale') or None
    kwargs = {}
    if locale:
        kwargs['locale'] = locale
    if Capabilities.WIDGET in remote_laboratory.get_capabilities():
        response = remote_laboratory.load_widget(reservation_id, widget_name, back = url_for('.reload', _external = True), **kwargs)
    else:
        response = {'url' : reservation_id}
    widget_contents_url = response['url']
    return redirect(widget_contents_url)
    
class RegistrationForm(Form):
    full_name  = TextField(lazy_gettext('School name'), [validators.Required(), validators.Length(min=4)] + forms.SCHOOL_FULL_NAME_VALIDATORS, description = lazy_gettext('School name.'))
    short_name = TextField(lazy_gettext('Short name'), [validators.Required()] + forms.SCHOOL_SHORT_NAME_VALIDATORS, description = lazy_gettext('Short name (lower case, all letters, dots and numbers).'))
    url        = TextField(lazy_gettext('School URL'), [validators.Length(min=6, max=200), validators.URL(), validators.Required()], description = lazy_gettext('Address of your school.'))
    user_full_name  = TextField(lazy_gettext('User name'), [validators.Required(), validators.Length(min=4)] + forms.USER_FULL_NAME_VALIDATORS, description = lazy_gettext('Your name and last name.'))
    user_login      = TextField(lazy_gettext('Login'), [validators.Required()] + forms.USER_LOGIN_DEFAULT_VALIDATORS, description = lazy_gettext('Your new login (you can create more later).'))
    user_password   = PasswordField(lazy_gettext('Password'), [validators.Required()] + forms.USER_PASSWORD_DEFAULT_VALIDATORS, description = lazy_gettext('Your access password.'))

@opensocial_blueprint.route("/register/", methods = ['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        errors = False
        if db.session.query(LearningTool).filter_by(name = form.short_name.data).first():
            form.short_name.errors.append(gettext('This name is already taken'))
            errors = True
        if db.session.query(LearningTool).filter_by(full_name = form.full_name.data).first():
            form.full_name.errors.append(gettext('This name is already taken'))
            errors = True
        if not errors:
            lt = LearningTool(name = form.short_name.data, full_name = form.full_name.data, url = form.url.data)
            shindig_credentials = ShindigCredentials(lt = lt, shindig_url = 'http://shindig2.epfl.ch')
            lt_user = LtUser(login = form.user_login.data, full_name = form.user_full_name.data, lt = lt, access_level = 'admin')
            lt_user.password = unicode(hashlib.new('sha', form.user_password.data.encode('utf8')).hexdigest())
            for lab in db.session.query(Laboratory).filter_by(available = True).all():
                permission_to_lt = PermissionToLt(lt = lt, laboratory = lab, local_identifier = lab.default_local_identifier)
                db.session.add(permission_to_lt)
            db.session.add(lt)
            db.session.add(shindig_credentials)
            db.session.add(lt_user)
            db.session.commit()
            return redirect(url_for('login_ple', next = url_for('ple_admin.index')) )
            
    return render_template("opensocial/registration.html", form = form)
