import json
import urllib2
import hashlib
import traceback
import threading

from flask import Blueprint, request, redirect, render_template, url_for
from flask.ext.wtf import Form, validators, TextField, PasswordField, ValidationError

from labmanager.db import db_session
from labmanager.models import LearningTool, PermissionToLt, LtUser, ShindigCredentials, Laboratory
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
    return render_template('/opensocial/widget.xml', public = False, institution_id = institution_id, lab_name = lab_name, widget_name = widget_name)

@opensocial_blueprint.route("/public/widgets/<lab_name>/widget_<widget_name>.xml")
def public_widget_xml(lab_name, widget_name):
    return render_template('/opensocial/widget.xml', public = True, lab_name = lab_name, widget_name = widget_name)

@opensocial_blueprint.route("/smartgateway/<institution_id>/<lab_name>/sg.js")
def smartgateway(institution_id, lab_name):
    return render_template("opensocial/smartgateway.js", public = False, institution_id = institution_id, lab_name = lab_name)

@opensocial_blueprint.route("/public/smartgateway/<lab_name>/sg.js")
def public_smartgateway(lab_name):
    return render_template("opensocial/smartgateway.js", public = True, lab_name = lab_name)



@opensocial_blueprint.route("/reservations/new/<institution_id>/<lab_name>/")
def reserve(institution_id, lab_name):
    return _reserve_impl(lab_name, False, institution_id)

@opensocial_blueprint.route("/public/reservations/new/<lab_name>/")
def public_reserve(lab_name):
    return _reserve_impl(lab_name, True, None)

def _reserve_impl(lab_name, public, institution_id):
    st = request.args.get('st') or ''

    if public:
        db_laboratory = db_session.query(Laboratory).filter_by(publicly_available = True, public_identifier = lab_name).first()
        if db_laboratory is None:
            return render_template("opensocial/errors.html", message = "That lab does not exist or it is not publicly available.")

        SHINDIG.url = 'http://shindig.epfl.ch'

        ple_configuration = '{}'
        institution_name  = 'public-labs' # TODO: make sure that this name is unique
        courses_configurations = []
    else:
        institution = db_session.query(LearningTool).filter_by(name = institution_id).first()
        if institution is None or len(institution.shindig_credentials) < 1:
            return render_template("opensocial/errors.html", message = "This is not a valid PLE. Make sure that the institution id is fine and that there are Shindig Credentials configured")

        SHINDIG.url = institution.shindig_credentials[0].shindig_url

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


        # Now, check permissions:
        # First, check if the lab is public (e.g. the lab can be accessed by anyone)
        # Second, check accesibility permissions (e.g. the lab is accessible for everyone from that institution without specifying any Graasp space). 
        # After that, in the case that there are not accesibility permissions, check for that institution if there is a permission identified by that lab_name, and check which courses (spaces in OpenSocial) have that permission.

        public_lab = db_session.query(Laboratory).filter_by(public_identifier = lab_name, publicly_available = True).first()
        courses_configurations = []
        
        if public_lab is None:
            # No public access is granted for the lab, check accesibility permissions
            accessible_permission = db_session.query(PermissionToLt).filter_by(lt = institution, local_identifier = lab_name, accessible = True).first()
            
            if accessible_permission is None:
                permission = db_session.query(PermissionToLt).filter_by(lt = institution, local_identifier = lab_name).first()
                if permission is None:
                    return render_template("opensocial/errors.html", message = "Your PLE is valid, but don't have permissions for the requested laboratory.")
                
                for course_permission in permission.course_permissions:
                    if course_permission.course.context_id in spaces:
                        # Let the server choose among the best possible configuration
                        courses_configurations.append(course_permission.configuration)

                if len(courses_configurations) == 0:
                    return render_template("opensocial/errors.html", message = "Your PLE is valid and your lab too, but you're not in one of the spaces that have permissions (you are in %r)" % spaces)

            else:
                # There is a accesibility permission for that lab and institution
                
                permission = accessible_permission

            ple_configuration = permission.configuration
            db_laboratory     = permission.laboratory
            institution_name  = institution.name

        else: 
            # There is a public permission for the lab
            ple_configuration = []
            db_laboratory     = public_lab
            institution_name  = institution.name            

            
    # Obtain user data
    try:
        current_user_str  = urllib2.urlopen(url_shindig("/rest/people/@me/@self?st=%s" % st)).read()
        current_user_data = json.loads(current_user_str)
    except:
        traceback.print_exc()
        return render_template("opensocial/errors.html", message = "Could not connect to %s." % url_shindig("/rest/people/@me/@self?st=%s" % st))

    # name    = current_user_data['entry'].get('displayName') or 'anonymous'
    user_id = current_user_data['entry'].get('id') or 'no-id'

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
                                                institution               = institution_name,
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
    return _open_widget_impl(lab_name, widget_name, False, institution_id)

@opensocial_blueprint.route("/public/reservations/existing/<lab_name>/<widget_name>/")
def open_public_widget(lab_name, widget_name):
    return _open_widget_impl(lab_name, widget_name, True, None)

def _open_widget_impl(lab_name, widget_name, public, institution_id):
    if public:
        db_laboratory = db_session.query(Laboratory).filter_by(publicly_available = True, public_identifier = lab_name).first()
    else:
        institution = db_session.query(LearningTool).filter_by(name = institution_id).first()
        if institution is None or len(institution.shindig_credentials) == 0:
            return "Institution not found or it does not support Shindig"

        permission = db_session.query(PermissionToLt).filter_by(lt = institution, local_identifier = lab_name).first()
        db_laboratory     = permission.laboratory if permission is not None else None

    if db_laboratory is None:
        return "Laboratory not found"
    db_rlms           = db_laboratory.rlms
    rlms_version      = db_rlms.version
    rlms_kind         = db_rlms.kind

    ManagerClass = get_manager_class(rlms_kind, rlms_version)
    remote_laboratory = ManagerClass(db_rlms.configuration)

    reservation_id = request.args.get('reservation_id') or 'reservation-id-not-found'
    response = remote_laboratory.load_widget(reservation_id, widget_name)
    widget_contents_url = response['url']
    return redirect(widget_contents_url)

class RegistrationForm(Form):

    full_name  = TextField('School name', [validators.Length(min=4, max=50), validators.Required()], description = "School name.")
    short_name = TextField('Short name', [validators.Length(min=4, max=15), validators.Required()], description = "Short name (lower case, all letters, dots and numbers).")
    url        = TextField('School URL', [validators.Length(min=6, max=200), validators.URL(), validators.Required()], description = "Address of your school.")

    user_full_name  = TextField('User name', [validators.Length(min=4, max=15), validators.Required()], description = "Your name and last name.")
    user_login      = TextField('Login', [validators.Length(min=4, max=15), validators.Required()], description = "Your new login (you can create more later).")
    user_password   = PasswordField('Password', [validators.Length(min=4, max=15), validators.Required()], description = "Your new login (you can create more later).")

    def validate_short_name(form, field):
        for c in field.data:
            if c not in 'abcdefghijklmnopqrstuvwxyz._0123456789':
                raise ValidationError('Invalid character found: %s' % c)

    validate_user_login = validate_short_name


@opensocial_blueprint.route("/register/", methods = ['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        errors = False
        if db_session.query(LearningTool).filter_by(name = form.short_name.data).first():
            form.short_name.errors.append("This name is already taken")
            errors = True
        if db_session.query(LearningTool).filter_by(full_name = form.full_name.data).first():
            form.full_name.errors.append("This name is already taken")
            errors = True
        if not errors:
            lt = LearningTool(name = form.short_name.data, full_name = form.full_name.data, url = form.url.data)
            shindig_credentials = ShindigCredentials(lt = lt, shindig_url = 'http://shindig.epfl.ch')
            lt_user = LtUser(login = form.user_login.data, full_name = form.user_full_name.data, lt = lt, access_level = 'admin')
            lt_user.password = unicode(hashlib.new('sha', form.user_password.data).hexdigest())

            for lab in db_session.query(Laboratory).filter_by(available = True).all():
                permission_to_lt = PermissionToLt(lt = lt, laboratory = lab, local_identifier = lab.default_local_identifier)
                db_session.add(permission_to_lt)

            db_session.add(lt)
            db_session.add(shindig_credentials)
            db_session.add(lt_user)
            db_session.commit()
            return redirect(url_for('login_lms', next = url_for('ple_admin.index')) )
        
    return render_template("opensocial/registration.html", form = form)

