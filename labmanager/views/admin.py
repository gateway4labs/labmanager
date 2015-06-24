# -*-*- encoding: utf-8 -*-*-

import json
import urlparse
import threading
import traceback

from hashlib import new as new_hash
from yaml import load as yload
from wtforms.fields import PasswordField
from flask import request, redirect, url_for, session, Markup, abort, Response, flash
from flask.ext import wtf
from flask.ext.wtf import Form
from flask.ext.login import current_user
from flask.ext.admin import Admin, BaseView, AdminIndexView, expose
from flask.ext.admin.model import InlineFormAdmin
from flask.ext.admin.contrib.sqlamodel import ModelView
from labmanager.babel import gettext, lazy_gettext
from labmanager.models import LabManagerUser, LtUser
from labmanager.models import PermissionToCourse, RLMS, Laboratory, PermissionToLt, RequestPermissionLT
from labmanager.models import BasicHttpCredentials, LearningTool, Course, PermissionToLtUser, ShindigCredentials
from labmanager.rlms import get_form_class, get_supported_types, get_supported_versions, get_manager_class, Capabilities
from labmanager.views import RedirectView
from labmanager.scorm import get_scorm_object, get_authentication_scorm
from labmanager.db import db
import labmanager.forms as forms
from labmanager.utils import data_filename, remote_addr
import labmanager.rlms.ext.rest as http_plugin

config = yload(open(data_filename('labmanager/config/config.yml')))

#####################################################################
# 
# 
#                      Parent views
# 
# 

class L4lModelView(ModelView):
    def is_accessible(self):
        if not current_user.is_authenticated():
            return False
        return session['usertype'] == 'labmanager'
    
    def _handle_view(self, name, **kwargs):
        if not self.is_accessible():
            return redirect(url_for('login_admin', next=request.url))
        return super(L4lModelView, self)._handle_view(name, **kwargs)

class L4lBaseView(BaseView):
    def is_accessible(self):
        if not current_user.is_authenticated():
            return False
        return session['usertype'] == 'labmanager'
    
    def _handle_view(self, name, **kwargs):
        if not self.is_accessible():
            return redirect(url_for('login_admin', next=request.url))
        return super(L4lBaseView, self)._handle_view(name, **kwargs)

class L4lAdminIndexView(AdminIndexView):
    def is_accessible(self):
        if not current_user.is_authenticated():
            return False
        return session['usertype'] == 'labmanager'
    
    def _handle_view(self, name, **kwargs):
        if not self.is_accessible():
            return redirect(url_for('login_admin', next=request.url))
        return super(L4lAdminIndexView, self)._handle_view(name, **kwargs)

##############################################################
# 
#     Main views
# 

class AdminPanel(L4lAdminIndexView):
    @expose()
    def index(self):
        return self.render("labmanager_admin/index.html")

class UsersPanel(L4lModelView):
    column_list = ['login', 'name']
    form_columns = ('name', 'login', 'password')
    column_labels = dict(name=lazy_gettext('name'), login=lazy_gettext('login'), password=lazy_gettext('password'))
    form_overrides = dict(access_level=wtf.SelectField, password=PasswordField)
    form_args = dict(login=dict(validators=forms.USER_LOGIN_DEFAULT_VALIDATORS[:]),
                           password=dict(validators=forms.USER_PASSWORD_DEFAULT_VALIDATORS[:]))       

    def __init__(self, session, **kwargs):
        super(UsersPanel, self).__init__(LabManagerUser, session, **kwargs)
        
    def create_model(self, form):
        if form.password.data == '':
            form.password.errors.append(lazy_gettext("This field is required."))
            return False            
        form.password.data = unicode(new_hash("sha", form.password.data.encode('utf8')).hexdigest())
        return super(UsersPanel, self).create_model(form)

    def update_model(self, form, model):
        old_password = model.password
        if form.password.data != '':
            form.password.data = unicode(new_hash("sha", form.password.data.encode('utf8')).hexdigest())
        return_value = super(UsersPanel, self).update_model(form, model)
        if form.password.data == '':
            model.password = old_password
            self.session.add(model)
            self.session.commit()
        return return_value

class LtUsersPanel(L4lModelView):
    column_list = ['lt', 'login', 'full_name', 'access_level']
    column_labels = dict(lt=lazy_gettext('lt'), login=lazy_gettext('login'), full_name=lazy_gettext('full_name'), access_level=lazy_gettext('access_level'))
    form_columns = ('full_name', 'login', 'password', 'access_level', 'lt')
    sel_choices = [(level, level.title()) for level in config['user_access_level']]
    form_overrides = dict(access_level=wtf.SelectField, password=PasswordField)
    form_args = dict(access_level=dict( choices=sel_choices ),
                            login=dict(validators=forms.USER_LOGIN_DEFAULT_VALIDATORS[:]),
                            password=dict(validators=forms.USER_PASSWORD_DEFAULT_VALIDATORS[:]))
    
    def __init__(self, session, **kwargs):
        super(LtUsersPanel, self).__init__(LtUser, session, **kwargs)

    def create_model(self, form):
        if form.password.data == '':
            form.password.errors.append(lazy_gettext("This field is required."))
            return False
        form.password.data = unicode(new_hash("sha", form.password.data.encode('utf8')).hexdigest())
        return super(LtUsersPanel, self).create_model(form)

    def update_model(self, form, model):
        old_password = model.password
        if form.password.data != '':
            form.password.data = unicode(new_hash("sha", form.password.data.encode('utf8')).hexdigest())
        return_value = super(LtUsersPanel, self).update_model(form, model)
        if form.password.data == '':
            model.password = old_password
            self.session.add(model)
            self.session.commit()
        return return_value

class PermissionToLtUsersPanel(L4lModelView):
    def __init__(self, session, **kwargs):
        super(PermissionToLtUsersPanel, self).__init__(PermissionToLtUser, session, **kwargs)

def accept_formatter(v, c, req, p):
    klass = 'btn-success'
    msg = lazy_gettext("Accept request")
    return Markup("""<form method='POST' action='%(url)s' style="text-align: center">
                        <input type='hidden' name='request_id' value='%(request_id)s'/>
                        <input class='btn %(klass)s' type='submit' value="%(msg)s"></input>
                    </form>""" % dict(
                        url                      = url_for('.accept_request'),                     
                        klass                    = klass,
                        msg                      = msg,
                        request_id               = req.id,
                    ))

def reject_formatter(v, c, req, p):
    klass = 'btn-danger'
    msg =  lazy_gettext('Reject request')
    return Markup("""<form method='POST' action='%(url)s' style="text-align: center">
                        <input class='btn %(klass)s' type='submit' value="%(msg)s"></input>
                        <input type='hidden' name='request_id' value='%(request_id)s'/>
                    </form>""" % dict(
                        url                      = url_for('.reject_request'),                     
                        klass                    = klass,
                        msg                      = msg,
                        request_id               = req.id,
                    ))

class LabRequestsPanel(L4lModelView):
    # 
    # TODO: manage configuration
    # 
    can_create = can_delete = can_edit = False
    column_list = ['laboratory', 'local_identifier', 'lt', 'accept', 'reject']
    column_labels = dict(laboratory=lazy_gettext('laboratory'), local_identifier=lazy_gettext('local_identifier'), lt=lazy_gettext('lt'), accept=lazy_gettext('accept'), reject=lazy_gettext('reject'))
    column_formatters = dict( accept = accept_formatter, reject  = reject_formatter )
    column_descriptions = dict(
                laboratory       = lazy_gettext(u"The laboratory that has been requested"),
                lt              = lazy_gettext(u"Learning Management System which created each request"),
                local_identifier = lazy_gettext(u"Unique identifier for a LT to access a laboratory"),
            )

    def __init__(self, session, **kwargs):
        super(LabRequestsPanel, self).__init__(RequestPermissionLT, session, **kwargs)

    @expose('/accept_request', methods = ['GET','POST'])
    def accept_request(self):
        request_id = unicode(request.form['request_id'])
        req = self.session.query(RequestPermissionLT).filter_by(id = request_id).first()
        perm = PermissionToLt(lt = req.lt, laboratory = req.laboratory, configuration = '', local_identifier = req.local_identifier)
        self.session.add(perm)    
        self.session.delete(req)
        self.session.commit()
        return redirect(url_for('.index_view'))

    @expose('/reject_request', methods = ['GET','POST'])
    def reject_request(self):
        request_id = unicode(request.form['request_id'])
        req = self.session.query(RequestPermissionLT).filter_by(id = request_id).first()
        perm = PermissionToLt(lt = req.lt, laboratory = req.laboratory, configuration = '', local_identifier = req.local_identifier)
        self.session.add(perm)    
        self.session.delete(req)
        self.session.commit()
        return redirect(url_for('.index_view'))
        
##############################################################
# 
#    LT related views
# 
class BasicHttpCredentialsForm(InlineFormAdmin):
    column_descriptions = dict(
            lt_login = lazy_gettext('Login of the LT when contacting the LabManager'),
        )
    form_overrides = dict(lt_password=PasswordField, labmanager_password=PasswordField)
    form_columns = ('id', 'lt_login', 'lt_password', 'lt_url', 'labmanager_login', 'labmanager_password')
    excluded_form_fields = ('id',)

def download(v, c, lt, p):
    if len(lt.basic_http_authentications) > 0:
            return Markup('<a href="%s"> Download </a>' % (url_for('.scorm_authentication', id = lt.id)))
    return gettext('N/A')

class LTPanel(L4lModelView):
    inline_models = (BasicHttpCredentialsForm(BasicHttpCredentials), ShindigCredentials)
    column_list = ['full_name', 'name', 'url', 'download']
    column_labels = dict(full_name=lazy_gettext('full_name'), name=lazy_gettext('name'), url=lazy_gettext('url'), download=lazy_gettext('download'))
    column_formatters = dict( download = download )
    column_descriptions = dict( name = lazy_gettext("Institution short name (lower case, all letters, dots and numbers)"), full_name = lazy_gettext("Name of the institution."))

    def __init__(self, session, **kwargs):
        super(LTPanel, self).__init__(LearningTool, session, **kwargs)
        self.local_data = threading.local()

    def edit_form(self, obj = None):
        form = super(LTPanel, self).edit_form(obj)
        self.local_data.basic_http_authentications = {}
        if obj is not None:
            for auth in obj.basic_http_authentications:
                self.local_data.basic_http_authentications[auth.id] = auth.lt_password
        return form

    def on_model_change(self, form, model):
        old_basic_http_authentications = getattr(self.local_data, 'basic_http_authentications', {})
        for authentication in model.basic_http_authentications:
            old_password = old_basic_http_authentications.get(authentication.id, None)
            authentication.update_password(old_password)

    @expose('/<id>/scorm_authentication.zip')
    def scorm_authentication(self, id):
        lt = self.session.query(LearningTool).filter_by(id = id).one()
        if lt.basic_http_authentications:
            url = lt.basic_http_authentications[0].lt_url or ''
        else:
            url = ''
        return get_authentication_scorm(url)
 
class CoursePanel(L4lModelView):
    def __init__(self, session, **kwargs):
        super(CoursePanel, self).__init__(Course, session, **kwargs)

##########################################################
# 
# 
#                   RLMS views
# 
class RLMSObject(object): pass

class RLMSPanel(L4lModelView):
    # For listing 
    column_list  = ['name', 'kind', 'version', 'location', 'url', 'labs','publicly_available']
    column_labels  = dict(name=lazy_gettext('name'), kind=lazy_gettext('kind'), version=lazy_gettext('version'), location=lazy_gettext('location'), url=lazy_gettext('url'), labs=lazy_gettext('labs'), publicly_available = lazy_gettext('public'))
    column_exclude_list = ('version','configuration')
    column_descriptions = {
        'location' : lazy_gettext('City and country where the RLMS is hosted'),
        'url'      : lazy_gettext('Main URL of the RLMS'),
    }

    column_formatters = dict(
            labs = lambda v, c, rlms, p: Markup('<a href="%s"> %s</a>' % (url_for('.labs', id=rlms.id), gettext("list"))),
            url = lambda v, c, rlms, p: Markup('<a href="%s" target="_blank">%s</a>' % (rlms.url, rlms.url))
        )

    def __init__(self, session, **kwargs):
        super(RLMSPanel, self).__init__(RLMS, session, **kwargs)
   
    @expose('/create/')
    def create_view(self):
        rlmss = []
        for ins_rlms in get_supported_types():
            for ver in get_supported_versions(ins_rlms):
                rlmss.append((ins_rlms, ver))
        return self.render("labmanager_admin/create-rlms.html", rlmss = rlmss)

    @expose('/create/<rlms>/<version>/', methods = ['GET', 'POST'])
    def create_rlms(self, rlms, version):
        supported_types = get_supported_types()
        if rlms not in supported_types:
            return "RLMS not found", 404
        supported_versions = get_supported_versions(rlms)
        if version not in supported_versions:
            return "RLMS version not found", 404

        return self._add_or_edit(rlms, version, True, None, {})

    @expose('/edit/', methods = ['GET', 'POST'])
    def edit_view(self):
        rlms_id = request.args.get('id')
        if not rlms_id:
            return "RLMS id not found", 404
        rlms = self.session.query(RLMS).filter_by(id = rlms_id).first()
        if not rlms:
            return "RLMS not found", 404

        config = json.loads(rlms.configuration)
        rlms_obj = RLMSObject()
        rlms_obj.name = rlms.name
        rlms_obj.url = rlms.url
        rlms_obj.location = rlms.location
        rlms_obj.publicly_available = rlms.publicly_available
        rlms_obj.public_identifier = rlms.public_identifier
        rlms_obj.default_autoload = rlms.default_autoload
        for key in config:
            setattr(rlms_obj, key, config[key])

        return self._add_or_edit(rlms.kind, rlms.version, False, rlms_obj, config)

    def _add_or_edit(self, rlms, version, add_or_edit, obj, config):
        edit_id = request.args.get('id')
        form_class = get_form_class(rlms, version)
        form = form_class(add_or_edit=add_or_edit, obj = obj)
        error_messages = []
        if form.validate_on_submit():
            configuration = config
            for key in form.get_field_names():
                if key not in dir(forms.AddForm):
                    field = getattr(form, key)
                    is_password = 'password' in unicode(field.type).lower()
                    # If we're editing, and this field is a password, do not change it
                    if is_password and not add_or_edit and field.data == '':
                        continue
                    configuration[key] = field.data
            config_json = json.dumps(configuration)
            
            current_rlms_id = None if add_or_edit else edit_id
            ManagerClass = get_manager_class(rlms, version, current_rlms_id)
            rlms_instance = ManagerClass(config_json)
            if hasattr(rlms_instance, 'test'):
                try:
                    error_messages = rlms_instance.test() or []
                except Exception as e:
                    error_messages.append(u'%s%s' % (gettext("Error testing the RLMS:"), e))
                    traceback.print_exc()

            if form.publicly_available.data and len(form.public_identifier.data) == 0:
                form.public_identifier.errors = [gettext("If the RLMS is public, it must have a public identifier")]
                error_messages.append(gettext("Invalid public identifier"))
            elif form.publicly_available.data and len(form.public_identifier.data) < 4:
                form.public_identifier.errors = [gettext("If the RLMS is public, it must have a public identifier with at least 4 characters")]
                error_messages.append(gettext("Invalid public identifier"))

            elif form.publicly_available.data: # If publicly available, retrieve existing RLMS with that public identifier
                existing_objects = self.session.query(RLMS).filter_by(public_identifier = form.public_identifier.data).all()
                if not add_or_edit: # If editing, don't count the one being edited
                    existing_objects = [ existing_obj for existing_obj in existing_objects if unicode(existing_obj.id) != unicode(edit_id)]
                if existing_objects:
                    form.public_identifier.errors = [gettext("That identifier is already taken")]
                    error_messages.append(gettext("Use other identifier or don't make the RLMS public"))


            if not error_messages:
                if add_or_edit:
                    rlms_obj = RLMS(kind = rlms, version = version, name = form.name.data,
                                url = form.url.data, location = form.location.data,
                                configuration = config_json, 
                                publicly_available = form.publicly_available.data,
                                public_identifier = form.public_identifier.data,
                                default_autoload = form.default_autoload.data)
                else:
                    rlms_obj = self.session.query(RLMS).filter_by(id = edit_id).first()
                    rlms_obj.url = form.url.data
                    rlms_obj.location = form.location.data
                    rlms_obj.name = form.name.data
                    rlms_obj.default_autoload = form.default_autoload.data
                    rlms_obj.publicly_available = form.publicly_available.data
                    rlms_obj.public_identifier = form.public_identifier.data
                    rlms_obj.configuration = config_json


                self.session.add(rlms_obj)
                try:
                    self.session.commit()
                except:
                    self.session.rollback()
                    raise
                
                if add_or_edit:
                    rlms_id = rlms_obj.id
                else:
                    rlms_id = edit_id
    
                labs_url = url_for('.labs', id = rlms_id, _external = True)
                if rlms == http_plugin.PLUGIN_NAME:
                    if add_or_edit:
                        # First, store the rlms identifier in the database in the context_id
                        configuration['context_id'] = rlms_id
                        config_json = json.dumps(configuration)
                        rlms_obj.configuration = config_json
                        try:
                            self.session.commit()
                        except:
                            self.session.rollback()
                            raise
                    
                    # Then, re-create the manager class and call setup
                    rlms_instance = ManagerClass(config_json)
                    
                    try:
                        setup_url = rlms_instance.setup(back_url = labs_url)
                    except Exception as e:
                        flash(gettext("Couldn't load the setup URL! (this usually means that the plug-in is not correctly configured). Error message: %s" % e))
                        return redirect(url_for('.edit_view', id = rlms_id))
                    else:
                        return redirect(setup_url)

                return redirect(labs_url)

        if not add_or_edit and rlms == http_plugin.PLUGIN_NAME:
            setup_url = url_for('.plugin_setup', rlms_id = edit_id)
        else:
            setup_url = None

        return self.render('labmanager_admin/create-rlms-step-2.html', name = rlms, version = version, form = form, fields = form.get_field_names(), error_messages = error_messages, edit_id = edit_id, setup_url = setup_url)

    @expose('/plugin-setup/<rlms_id>/', methods = ['GET', 'POST'])
    def plugin_setup(self, rlms_id):
        rlms_obj = self.session.query(RLMS).filter_by(id = rlms_id).first()
        if not rlms_obj:
            return "RLMS not found", 404
        if rlms_obj.kind != http_plugin.PLUGIN_NAME:
            return "RLMS is not HTTP", 400

        ManagerClass = get_manager_class(rlms_obj.kind, rlms_obj.version, rlms_obj.id)
        rlms_instance = ManagerClass(rlms_obj.configuration)
        back_url = url_for('.edit_view', id = rlms_id, _external = True)

        try:
            setup_url = rlms_instance.setup(back_url = back_url)
        except Exception as e:
            flash(gettext("Couldn't load the setup URL! (this usually means that the plug-in is not correctly configured). Error message: %s" % e))
            return redirect(back_url)
        else:
            return redirect(setup_url)



    @expose('/labs/<id>/', methods = ['GET','POST'])
    def labs(self, id):
        # 
        # TODO: CSRF is not used here. Security hole
        # 
        rlms_db = self.session.query(RLMS).filter_by(id = id).first()
        if rlms_db is None:
            return abort(404)

        query = request.args.get('q')
        if query is not None:
            page = request.args.get('p', '1')
            try:
                page = int(page)
            except:
                page = 1
        else:
            page = 1

        RLMS_CLASS = get_manager_class(rlms_db.kind, rlms_db.version, rlms_db.id)
        rlms = RLMS_CLASS(rlms_db.configuration)
        if query:
            query_results = rlms.search(query = query, page = page)
            labs = query_results['laboratories']
            force_search = False
            number_of_pages = query_results.get('pages', 1)
            pages = []
            if number_of_pages > 1:
                for p in xrange(1, number_of_pages + 1):
                    obj = {
                        'label' : unicode(p),
                        'link'  : url_for('.labs', id = id, q = query, p = p)
                    }
                    obj['active'] = (p != page)
                    pages.append(obj)
        else:
            query_results = {}
            labs = rlms.get_laboratories()
            capabilities = rlms.get_capabilities()
            force_search = Capabilities.FORCE_SEARCH in capabilities
            pages = []

        registered_labs = [ lab.laboratory_id for lab in rlms_db.laboratories ]
        if request.method == 'POST':
            selected = []
            for name, value in request.form.items():
                if name != 'action' and value == 'on':
                    for lab in labs:
                        if lab.laboratory_id == name:
                            selected.append(lab)
            changes = False
            if request.form['action'] == 'register':
                for lab in selected:
                    if not lab.laboratory_id in registered_labs:
                        self.session.add(Laboratory(name = lab.name, laboratory_id = lab.laboratory_id, rlms = rlms_db))
                        changes = True
            elif request.form['action'] == 'unregister':
                for lab in selected:
                    if lab.laboratory_id in registered_labs:
                        cur_lab_db = None
                        for lab_db in rlms_db.laboratories:
                            if lab_db.laboratory_id == lab.laboratory_id:
                                cur_lab_db = lab_db
                                break
                        if cur_lab_db is not None:
                            self.session.delete(cur_lab_db)
                            changes = True
            if changes:
                self.session.commit()
        registered_labs = [ lab.laboratory_id for lab in rlms_db.laboratories ]
        return self.render('labmanager_admin/lab-list.html', rlms = rlms_db, labs = labs, registered_labs = registered_labs, query = query, force_search = force_search, pages = pages, page = page, id = id)

def accessibility_formatter(v, c, lab, p):
    if lab.available:
        klass = 'btn-danger'
        msg = gettext('Make not available')
        return Markup("""<form method='POST' action='%(url)s' style="text-align: center">
                        <input type='hidden' name='activate' value='%(activate_value)s'/>
                        <input type='hidden' name='lab_id' value='%(lab_id)s'/>
                        <label> %(texto)s </label>
                        <input disabled type='text' name='default_local_identifier' value='%(default_local_identifier)s' style='width: 150px'/>
                        <input class='btn %(klass)s' type='submit' value="%(msg)s"></input>
                    </form>""" % dict(
                        url                      = url_for('.change_accessibility'),
                        activate_value           = unicode(lab.available).lower(),
                        lab_id                   = lab.id,
                        texto                    = gettext('Default local identifier:'),
                        klass                    = klass,
                        msg                      = msg,
                        default_local_identifier = lab.default_local_identifier,
                    ))
    else:
        klass = 'btn-success'
        msg = gettext('Make available')
    return Markup("""<form method='POST' action='%(url)s' style="text-align: center">
                        <input type='hidden' name='activate' value='%(activate_value)s'/>
                        <input type='hidden' name='lab_id' value='%(lab_id)s'/>
                        <label> %(texto)s </label>
                        <input type='text' name='default_local_identifier' value='%(default_local_identifier)s' style='width: 150px'/>
                        <input class='btn %(klass)s' type='submit' value="%(msg)s"></input>
                    </form>""" % dict(
                        url                      = url_for('.change_accessibility'),
                        activate_value           = unicode(lab.available).lower(),
                        lab_id                   = lab.id,
                        texto                    = gettext('Default local identifier:'),
                        klass                    = klass,
                        msg                      = msg,
                        default_local_identifier = lab.default_local_identifier,
                    ))

def public_availability_formatter(v, c, lab, p):
    if lab.publicly_available:
        klass = 'btn-danger'
        msg = gettext('Make not publicly available')
        return Markup("""<form method='POST' action='%(url)s' style="text-align: center">
                        <input type='hidden' name='activate' value='%(activate_value)s'/>
                        <input type='hidden' name='lab_id' value='%(lab_id)s'/>
                        <label> %(texto)s </label>
                        <input disabled type='text' name='public_identifier' value='%(public_identifier)s' style='width: 150px'/>
                        <input class='btn %(klass)s' type='submit' value="%(msg)s"></input>
                    </form>""" % dict(
                        url               = url_for('.change_public_availability'),
                        activate_value    = unicode(lab.publicly_available).lower(),
                        lab_id            = lab.id,
                        texto             = gettext('Public identifier:'),
                        klass             = klass,
                        msg               = msg,
                        public_identifier = lab.public_identifier,
                    ))
    else:
        klass = 'btn-success'
        msg = gettext('Make publicly available')

    return Markup("""<form method='POST' action='%(url)s' style="text-align: center">
                        <input type='hidden' name='activate' value='%(activate_value)s'/>
                        <input type='hidden' name='lab_id' value='%(lab_id)s'/>
                        <label> %(texto)s </label>
                        <input type='text' name='public_identifier' value='%(public_identifier)s' style='width: 150px'/>
                        <input class='btn %(klass)s' type='submit' value="%(msg)s"></input>
                    </form>""" % dict(
                        url               = url_for('.change_public_availability'),
                        activate_value    = unicode(lab.publicly_available).lower(),
                        lab_id            = lab.id,
                        texto             = gettext('Public identifier:'),
                        klass             = klass,
                        msg               = msg,
                        public_identifier = lab.public_identifier,
                    ))


def go_lab_reservation_formatter(v, c, lab, p):
    if lab.go_lab_reservation:
        klass = 'btn-danger'
        msg = gettext('Deactivate')
    else:
        klass = 'btn-success'
        msg = gettext('Activate')
    return Markup("""<form method='POST' action='%(url)s' style="text-align: center"> 
                <input type='hidden' name='activate' value='%(activate_value)s'/>
                <input type='hidden' name='lab_id' value='%(lab_id)s'/>
                <label> %(texto)s </label>
                <br>
                <input class='btn %(klass)s' type='submit' value="%(msg)s"></input>
                </form>""" % dict(
                    url = url_for('.change_go_lab_reservation'),
                    texto = gettext('Go-Lab Reservation'),
                    activate_value    = unicode(lab.go_lab_reservation).lower(),
                    lab_id            = lab.id,
                    klass = klass,
                    msg = msg  
                ))

def test_lab_formatter(v, c, lab, p):
    return Markup("""<label>%s</label><a class='btn btn-success' href="%s">%s</a>""" % (lazy_gettext("Test laboratory"), url_for('.test_lab', id = lab.id), lazy_gettext("Test")))


class LaboratoryPanel(L4lModelView):

    can_create = can_edit = False
    column_list = ['rlms', 'name', 'laboratory_id', 'visibility', 'availability', 'public_availability','go_lab_reservation', 'test']
    column_labels = dict(rlms=lazy_gettext('rlms'), name=lazy_gettext('name'), laboratory_id=lazy_gettext('laboratory_id'), visibility=lazy_gettext('visibility'), availability=lazy_gettext('availability'), public_availability=lazy_gettext('public_availability'),go_lab_reservation=lazy_gettext('Go-Lab reservation'), test=lazy_gettext("Test"))
    column_formatters = dict(availability = accessibility_formatter, public_availability = public_availability_formatter, go_lab_reservation = go_lab_reservation_formatter, test = test_lab_formatter)
    column_descriptions = dict(
                            availability = lazy_gettext("Make this laboratory automatically available for the Learning Tools"),
                            public_availability = lazy_gettext("Make this laboratory automatically available even from outside the registered Learning Tools"),
                            go_lab_reservation = lazy_gettext("Make this laboratory available to Go-Lab booking system"),
                            test = lazy_gettext("Test this laboratory"),
                    )

    def __init__(self, session, **kwargs):
        super(LaboratoryPanel, self).__init__(Laboratory, session, **kwargs)

    @expose('/lab/availability/local', methods = ['POST'])
    def change_accessibility(self):
        lab_id = int(request.form['lab_id'])
        activate = request.form['activate'] == 'true'
        lab = self.session.query(Laboratory).filter_by(id = lab_id).first()
        if lab is not None:
            if activate:
                lab.available = not activate
                lab.default_local_identifier = u""
            else:
                local_id = request.form['default_local_identifier']
                local_id = local_id.lstrip(' ')
                local_id = local_id.strip(' ')
                if not activate and len(local_id) == 0:
                    flash(gettext("Invalid local identifier (empty)"))
                    return redirect(url_for('.index_view'))
                existing_labs = self.session.query(Laboratory).filter_by(default_local_identifier=local_id).all()
                if len(existing_labs) > 0 and lab not in existing_labs:
                    flash(gettext(u"Local identifier '%(localidentifier)s' already exists", localidentifier=local_id))
                    return redirect(url_for('.index_view'))
                lab.available = not activate
                lab.default_local_identifier = local_id
            self.session.add(lab)
            self.session.commit()
        return redirect(url_for('.index_view'))

    @expose('/lab/test/')
    def test_lab(self):
        lab_id = request.args.get('id')
        lab = self.session.query(Laboratory).filter_by(id = lab_id).first()
        if lab is None:
            return "Laboratory id not found", 404

        return self.render("labmanager_admin/test-lab.html", lab = lab)

    @expose('/lab/test/display/')
    def display_lab(self):
        try:
            lab_id = int(request.args.get('id', '-1'))
        except ValueError:
            return "id must be an integer", 400
        
        lab = self.session.query(Laboratory).filter_by(id = lab_id).first()
        if lab is None:
            return "Laboratory id not found", 404

        return self.render("labmanager_admin/display_lab.html", laboratory = lab)

    @expose('/lab/test/launch/', methods = ['POST'])
    def launch_lab(self):
        lab_id = request.args.get('id')
        lab = self.session.query(Laboratory).filter_by(id = lab_id).first()
        if lab is None:
            return "Laboratory id not found", 404

        db_rlms = lab.rlms
        ManagerClass = get_manager_class(db_rlms.kind, db_rlms.version, db_rlms.id)
        remote_laboratory = ManagerClass(db_rlms.configuration)
        back_url = url_for('.display_lab', id = lab_id)
        try:
            response = remote_laboratory.reserve(lab.laboratory_id,
                                             current_user.login,
                                             "admin-panel",
                                             "{}",
                                             [],
                                             {},
                                             { 
                                                'user_agent' : unicode(request.user_agent),
                                                'from_ip'    : remote_addr(),
                                                'referer'    : request.referrer,
                                            }, back_url = back_url, debug = True)

            load_url = response['load_url']
        except Exception as e:
            flash(gettext("There was a problem testing this experiment. Error message: %s" % e))
            return redirect(back_url)
        return redirect(load_url)

    @expose('/lab/availability/public', methods = ['POST'])
    def change_public_availability(self):
        lab_id   = int(request.form['lab_id'])
        activate = request.form['activate'] == "true"
        lab = self.session.query(Laboratory).filter_by(id = lab_id).first()
        if lab is not None:
            if activate:
                lab.publicly_available = not activate
                lab.public_identifier = u""
            else:
                public_id = request.form['public_identifier']
                public_id = public_id.lstrip(' ')
                public_id = public_id.strip(' ')
                if not activate and len(public_id) == 0:
                    flash(gettext("Invalid public identifier (empty)"))
                    return redirect(url_for('.index_view'))
                existing_labs = self.session.query(Laboratory).filter_by(public_identifier=public_id).all()
                if len(existing_labs) > 0 and lab not in existing_labs:
                    flash(gettext(u"Public identifier '%(publicidentifier)s' already exists", publicidentifier=public_id))
                    return redirect(url_for('.index_view'))
                lab.publicly_available = not activate
                lab.public_identifier = public_id
            self.session.add(lab)
            self.session.commit()
        return redirect(url_for('.index_view'))

    @expose('/lab/golabreservation', methods = ['POST'])
    def change_go_lab_reservation(self):
        lab_id = int(request.form['lab_id'])
        activate = request.form['activate'] == 'true'
        lab = self.session.query(Laboratory).filter_by(id = lab_id).first()
        if lab is not None:
            if activate:
                lab.go_lab_reservation = not activate
            else:
                lab.go_lab_reservation = not activate
            self.session.add(lab)
            self.session.commit()
        return redirect(url_for('.index_view'))


def scorm_formatter(v, c, permission, p):
    if permission.lt.basic_http_authentications:
        return Markup('<a href="%s"> Download </a>' % (url_for('.get_scorm', lt_id = permission.lt.id,  local_id = permission.local_identifier)))
    return 'N/A'

class PermissionToLtPanel(L4lModelView):
    # 
    # TODO: manage configuration
    # 
    column_list = ['laboratory', 'lt', 'local_identifier', 'configuration', 'SCORM']
    column_labels = dict(laboratory=lazy_gettext('laboratory'), lt=lazy_gettext('lt'), local_identifier=lazy_gettext('local_identifier'), configuration=lazy_gettext('configuration'), SCORM=lazy_gettext('SCORM'))
    column_descriptions = dict(
                laboratory       = lazy_gettext(u"Laboratory"),
                lt               = lazy_gettext(u"Learning Management System"),
                local_identifier = lazy_gettext(u"Unique identifier for a Learning Tool to access a laboratory"),
            )
    column_formatters = dict( SCORM = scorm_formatter )

    def __init__(self, session, **kwargs):
        super(PermissionToLtPanel, self).__init__(PermissionToLt, session, **kwargs)

    @expose('/scorm/<lt_id>/scorm_<local_id>.zip')
    def get_scorm(self, lt_id, local_id):
        permission = self.session.query(PermissionToLt).filter_by(lt_id = lt_id, local_identifier = local_id).one()
        db_lt = permission.lt
        if db_lt.basic_http_authentications:
            url = db_lt.basic_http_authentications[0].lt_url or ''
        else:
            url = ''
        lt_path = urlparse.urlparse(url).path or '/'
        extension = '/'
        if 'gateway4labs/' in lt_path:
            extension = lt_path[lt_path.rfind('gateway4labs/lms/list') + len('gateway4labs/lms/list'):]
            lt_path  = lt_path[:lt_path.rfind('gateway4labs/')]
        contents = get_scorm_object(False, local_id, lt_path, extension)
        return Response(contents, headers = {'Content-Type' : 'application/zip', 'Content-Disposition' : 'attachment; filename=scorm_%s.zip' % local_id})
   
class PermissionPanel(L4lModelView):
    def __init__(self, session, **kwargs):
        super(PermissionPanel, self).__init__(PermissionToCourse, session, **kwargs)

##########################################################
# 
#                     Initialization
# 

def init_admin(app):
    admin_url = '/admin'
    admin = Admin(index_view = AdminPanel(url=admin_url), name = lazy_gettext(u"Lab Manager"), url = admin_url, endpoint = admin_url)
    i18n_LMSmngmt = lazy_gettext(u'LT Management')
    admin.add_view(LTPanel(db.session,        category = i18n_LMSmngmt, name = lazy_gettext(u"LT"),     endpoint = 'lt/lt'))
    admin.add_view(PermissionToLtPanel(db.session, category = i18n_LMSmngmt, name = lazy_gettext(u"LT Permissions"),    endpoint = 'lt/permissions'))
    admin.add_view(LtUsersPanel(db.session,   category = i18n_LMSmngmt, name = lazy_gettext(u"LT Users"),        endpoint = 'lt/users'))
    admin.add_view(LabRequestsPanel(db.session,   category = i18n_LMSmngmt, name = lazy_gettext(u"LT Requests"),        endpoint = 'lt/requests'))
    i18n_ReLMSmngmt = lazy_gettext(u'ReLMS Management')
    admin.add_view(RLMSPanel(db.session,       category = i18n_ReLMSmngmt, name = lazy_gettext(u"RLMS"),            endpoint = 'rlms/rlms'))
    admin.add_view(LaboratoryPanel(db.session, category = i18n_ReLMSmngmt, name = lazy_gettext(u"Registered labs"), endpoint = 'rlms/labs'))
    admin.add_view(UsersPanel(db.session,      category = lazy_gettext(u'Users'), name = lazy_gettext(u"Labmanager Users"), endpoint = 'users/labmanager'))
    admin.add_view(RedirectView('logout',      name = lazy_gettext(u"Log out"), endpoint = 'admin/logout'))
    admin.init_app(app)
