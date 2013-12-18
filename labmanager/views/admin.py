# -*-*- encoding: utf-8 -*-*-

import json
import urlparse
import threading

from hashlib import new as new_hash
from yaml import load as yload


from wtforms.fields import PasswordField

from flask import request, redirect, url_for, session, Markup, abort, Response, flash

from flask.ext import wtf
from flask.ext.wtf import validators

from flask.ext.login import current_user

from flask.ext.admin import Admin, BaseView, AdminIndexView, expose
from flask.ext.admin.model import InlineFormAdmin
from flask.ext.admin.contrib.sqlamodel import ModelView
from labmanager.babel import gettext, ngettext, lazy_gettext

from labmanager.models import LabManagerUser, LtUser

from labmanager.models import PermissionToCourse, RLMS, Laboratory, PermissionToLt, RequestPermissionLT
from labmanager.models import BasicHttpCredentials, LearningTool, Course, PermissionToLtUser, ShindigCredentials
from labmanager.rlms import get_form_class, get_supported_types, get_supported_versions, get_manager_class
from labmanager.views import RedirectView
from labmanager.scorm import get_scorm_object, get_authentication_scorm
import labmanager.forms as forms


config = yload(open('labmanager/config/config.yml'))

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
 #   form_args = dict(login=dict(validators=[validators.Length(min=5), validators.Regexp("^[a-z\._0-9]*$")]),
 #                           password=dict(validators=[validators.Optional(), validators.Length(min=8), validators.Regexp("[^\s]"]))
 
    form_args = dict(login=dict(validators=forms.USER_LOGIN_DEFAULT_VALIDATORS),
 #                           password=dict(validators=forms.USER_PASSWORD_DEFAULT_VALIDATORS))
                            password=dict(validators=[validators.Optional(), forms.USER_PASSWORD_DEFAULT_VALIDATORS]))           

    def __init__(self, session, **kwargs):
        super(UsersPanel, self).__init__(LabManagerUser, session, **kwargs)
        
    def create_model(self, form):

        if form.password.data == '':
            form.password.errors.append(lazy_gettext("This field is required."))
            return False

        form.password.data = new_hash("sha", form.password.data).hexdigest()
        return super(UsersPanel, self).create_model(form)

    def update_model(self, form, model):
        print "Estoy en update model"
        old_password = model.password
        if form.password.data != '':
            print "se cambia la password"
            form.password.data = new_hash("sha", form.password.data).hexdigest()
            
        return_value = super(UsersPanel, self).update_model(form, model)
        
        if form.password.data == '':
            model.password = old_password
            print "se mantiene la password antigua"
            self.session.add(model)
            self.session.commit()
        return return_value

class LtUsersPanel(L4lModelView):

    column_list = ['lt', 'login', 'full_name', 'access_level']
    column_lists = dict(lt=lazy_gettext('lt'), login=lazy_gettext('login'), full_name=lazy_gettext('full_name'), access_level=lazy_gettext('access_level'))

    def __init__(self, session, **kwargs):
        super(LtUsersPanel, self).__init__(LtUser, session, **kwargs)

    form_columns = ('full_name', 'login', 'password', 'access_level', 'lt')
    sel_choices = [(level, level.title()) for level in config['user_access_level']]
    form_overrides = dict(access_level=wtf.SelectField, password=PasswordField)
    form_args = dict( access_level=dict( choices=sel_choices ) )

    def on_model_change(self, form, model):
        # TODO: don't update password always
        model.password = new_hash("sha", model.password).hexdigest()


class PermissionToLtUsersPanel(L4lModelView):

    def __init__(self, session, **kwargs):
        super(PermissionToLtUsersPanel, self).__init__(PermissionToLtUser, session, **kwargs)



def accept_formatter(v, c, req, p):
    
    klass = 'btn-success'
    msg = 'Accept request'
                    
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
    msg = 'Reject request'
 
                   
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

class DynamicSelectWidget(wtf.widgets.Select):
    def __call__(self, *args, **kwargs):
        html = super(DynamicSelectWidget, self).__call__(*args, **kwargs)
        html = html.replace('<select ', '''<select onchange="document.location.replace(new String(document.location).replace(/&rlms=[^&]*/,'') + '&rlms=' + this.value)"''')
        return html

class DynamicSelectField(wtf.SelectField):
    widget = DynamicSelectWidget()


def _generate_choices():
    sel_choices = [('','')]
    for ins_rlms in get_supported_types():
        for ver in get_supported_versions(ins_rlms):
            sel_choices.append(("%s<>%s" % (ins_rlms, ver),"%s - %s" % (ins_rlms.title(), ver)) )
    return sel_choices

class RLMSPanel(L4lModelView):

    # For editing
    form_columns = ('kind', 'location', 'url')
    form_overrides = dict(kind=DynamicSelectField)

    # For listing 
    # column_list  = [lazy_gettext('kind'), lazy_gettext('version'), lazy_gettext('location'), lazy_gettext('url'), lazy_gettext('labs')]
    column_list  = ['kind', 'version', 'location', 'url', 'labs']
    column_labels  = dict(kind=lazy_gettext('kind'), version=lazy_gettext('version'), location=lazy_gettext('location'), url=lazy_gettext('url'), labs=lazy_gettext('labs'))
    column_exclude_list = (lazy_gettext('version'), lazy_gettext('configuration'))

    column_formatters = dict(
            labs = lambda v, c, rlms, p: Markup('<a href="%s"> %s</a>' % (url_for('.labs', id=rlms.id), list))
        )

    def __init__(self, session, **kwargs):
        super(RLMSPanel, self).__init__(RLMS, session, **kwargs)
        
        # 
        # For each supported RLMS, it provides a different edition
        # form. So as to avoid creating a new class each type for 
        # the particular form required, we must create a cache of
        # form classes.
        #
        self.__create_form_classes = {}
   
    def _get_cached_form_class(self, rlms, form):
        if rlms in self.__create_form_classes:
            form_class = self.__create_form_classes[rlms]
        else:
            # If it does not exist, we find the RLMS creation form
            rlmstype, rlmsversion = rlms.split('<>')
            rlms_form_class = get_form_class(rlmstype, rlmsversion)
            
            # And we create and register a new class for it
            class form_class(rlms_form_class, form.__class__):
                pass
            self.__create_form_classes[rlms] = form_class
        return form_class

    def _fill_form_instance(self, form, old_form, obj):
        form.csrf_token.data = old_form.csrf_token.data
        form.process(obj=obj)
        form.csrf_token.data = old_form.csrf_token.data

        for key in form.get_field_names():
            if key in request.form:
                getattr(form, key).data = request.form[key]

    def create_form(self, obj = None, *args, **kwargs):
        form = super(RLMSPanel, self).create_form(*args, **kwargs)
        rlms = request.args.get('rlms')

        if rlms is not None and '<>' in rlms:
            form_class = self._get_cached_form_class(rlms, form)

            old_form = form
            form = form_class(add_or_edit=True, fields=form._fields)
            form.kind.default = rlms
            self._fill_form_instance(form, old_form, obj)
        form.kind.choices = _generate_choices()
        return form

    def edit_form(self, obj, *args, **kwargs):
        form = super(RLMSPanel, self).edit_form(*args, **kwargs)
        form_class = self._get_cached_form_class(obj.kind + u'<>' + obj.version , form)
        old_form = form
        form = form_class(add_or_edit=False, fields=form._fields)
        del form.kind
        
        configuration = json.loads(obj.configuration)
        for key in configuration:
            # TODO: this should be RLMS specific
            if 'password' not in key: 
                setattr(obj, key, configuration[key])

        self._fill_form_instance(form, old_form, obj )
        return form

    def on_model_change(self, form, model):
        if model.kind == '':
            abort(406)
        
        if '<>' in model.kind:
            rlms_ver = model.kind.split('<>')
            model.kind, model.version = rlms_ver[0], rlms_ver[1]

        if not model.configuration:
            other_data = {}
        else:
            other_data = json.loads(model.configuration)

        for key in form.get_field_names():
            if key not in RLMSPanel.form_columns:
                # TODO: this should be RLMS specific
                if 'password' in key and getattr(form, key).data == '':
                    pass # Passwords can be skipped
                else:
                    other_data[key] = getattr(form, key).data
        
        model.configuration = json.dumps(other_data)

    @expose('/labs/<id>/', methods = ['GET','POST'])
    def labs(self, id):
        # 
        # TODO: CSRF is not used here. Security hole
        # 

        rlms_db = self.session.query(RLMS).filter_by(id = id).first()
        if rlms_db is None:
            return abort(404)

        RLMS_CLASS = get_manager_class(rlms_db.kind, rlms_db.version)
        rlms = RLMS_CLASS(rlms_db.configuration)
        labs = rlms.get_laboratories()

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

        return self.render('labmanager_admin/lab-list.html', rlms = rlms_db, labs = labs, registered_labs = registered_labs)

def accessibility_formatter(v, c, lab, p):

    if lab.available:
        klass = 'btn-danger'
        msg = gettext('Make not available')
    else:
        klass = 'btn-success'
        msg = gettext('Make available')

    return Markup("""<form method='POST' action='%(url)s' style="text-align: center">
                        <input type='hidden' name='activate' value='%(activate_value)s'/>
                        <input type='hidden' name='lab_id' value='%(lab_id)s'/>
                        <label>Default local identifier: </label>
                        <input type='text' name='local_identifier' value='%(default_local_identifier)s' style='width: 150px'/>
                        <input class='btn %(klass)s' type='submit' value="%(msg)s"></input>
                    </form>""" % dict(
                        url                      = url_for('.change_accessibility'),
                        activate_value           = unicode(lab.available).lower(),
                        lab_id                   = lab.id,
                        klass                    = klass,
                        msg                      = msg,
                        default_local_identifier = lab.default_local_identifier,
                    ))

def public_availability_formatter(v, c, lab, p):

    if lab.publicly_available:
        klass = 'btn-danger'
        msg = gettext('Make not publicly available')
    else:
        klass = 'btn-success'
        msg = gettext('Make publicly available')

    return Markup("""<form method='POST' action='%(url)s' style="text-align: center">
                        <input type='hidden' name='activate' value='%(activate_value)s'/>
                        <input type='hidden' name='lab_id' value='%(lab_id)s'/>
                        <label>Public identifier: </label>
                        <input type='text' name='public_identifier' value='%(public_identifier)s' style='width: 150px'/>
                        <input class='btn %(klass)s' type='submit' value="%(msg)s"></input>
                    </form>""" % dict(
                        url               = url_for('.change_public_availability'),
                        activate_value    = unicode(lab.publicly_available).lower(),
                        lab_id            = lab.id,
                        klass             = klass,
                        msg               = msg,
                        public_identifier = lab.public_identifier,
                    ))


class LaboratoryPanel(L4lModelView):

    can_create = can_edit = False

    column_list = ['rlms', 'name', 'laboratory_id', 'visibility', 'availability', 'public_availability']
    column_lables = dict(rlms=lazy_gettext('rlms'), name=lazy_gettext('name'), laboratory_id=lazy_gettext('laboratory_id'), visibility=lazy_gettext('visibility'), availability=lazy_gettext('availability'), public_availability=lazy_gettext('public_availability'))
    column_formatters = dict(availability = accessibility_formatter, public_availability = public_availability_formatter)
    column_descriptions = dict(
                            availability = lazy_gettext("Make this laboratory automatically available for the Learning Tools"),
                            public_availability = lazy_gettext("Make this laboratory automatically available even from outside the registered Learning Tools")
                    )

    def __init__(self, session, **kwargs):
        super(LaboratoryPanel, self).__init__(Laboratory, session, **kwargs)

    @expose('/lab/availability/local', methods = ['POST'])
    def change_accessibility(self):
        lab_id   = int(request.form['lab_id'])
        activate = request.form['activate'] == 'true'
        lab = self.session.query(Laboratory).filter_by(id = lab_id).first()
        if lab is not None:
            existing_labs = self.session.query(Laboratory).filter_by(default_local_identifier = request.form['local_identifier']).all()
            if len(existing_labs) > 0:
                # If there is more than one, then it's not only lab; and if there is only one but it's not this one, the same
                if len(existing_labs) > 1 or lab not in existing_labs:
                    flash(gettext(u"Local identifier '%(localidentifier)s' already exists"), localidentifier=request.form['local_identifier'])
                    return redirect(url_for('.index_view'))
            lab.available = not activate
            lab.default_local_identifier = request.form['local_identifier']
            if lab.available and len(lab.default_local_identifier) == 0:
                flash(gettext(u"Invalid local identifier (empty)"))
            else:
                self.session.add(lab)
                self.session.commit()
        return redirect(url_for('.index_view'))

    @expose('/lab/availability/public', methods = ['POST'])
    def change_public_availability(self):
        lab_id   = int(request.form['lab_id'])
        activate = request.form['activate'] == 'true'
        lab = self.session.query(Laboratory).filter_by(id = lab_id).first()
        if lab is not None:
            existing_labs = self.session.query(Laboratory).filter_by(public_identifier = request.form['public_identifier']).all()
            if len(existing_labs) > 0:
                # If there is more than one, then it's not only lab; and if there is only one but it's not this one, the same
                if len(existing_labs) > 1 or lab not in existing_labs:
                    flash(gettext(u"Public identifier '%(publicidentifier)s' already exists"), publicidentifier=request.form['public_identifier'])
                    return redirect(url_for('.index_view'))
            lab.publicly_available = not activate
            lab.public_identifier = request.form['public_identifier']
            print "testing..."
            if lab.publicly_available and len(lab.public_identifier) == 0:
                print "shait..."
                flash(gettext("Invalid public identifier (empty)"))
            else:
                self.session.add(lab)
                self.session.commit()
        return redirect(url_for('.index_view'))


def scorm_formatter(v, c, permission, p):
    
    if permission.lt.basic_http_authentications:
        return Markup('<a href="%s"> gettext("Download")</a>' % (url_for('.get_scorm', lt_id = permission.lt.id,  local_id = permission.local_identifier)))

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

def init_admin(app, db_session):
    admin_url = '/admin'

    admin = Admin(index_view = AdminPanel(url=admin_url), name = lazy_gettext(u"Lab Manager"), url = admin_url, endpoint = admin_url)
    i18n_LMSmngmt = lazy_gettext(u'LT Management')
    admin.add_view(LTPanel(db_session,        category = i18n_LMSmngmt, name = lazy_gettext(u"LT"),     endpoint = 'lt/lt'))
    admin.add_view(PermissionToLtPanel(db_session, category = i18n_LMSmngmt, name = lazy_gettext(u"LT Permissions"),    endpoint = 'lt/permissions'))
    admin.add_view(LtUsersPanel(db_session,   category = i18n_LMSmngmt, name = lazy_gettext(u"LT Users"),        endpoint = 'lt/users'))
    admin.add_view(LabRequestsPanel(db_session,   category = i18n_LMSmngmt, name = lazy_gettext(u"LT Requests"),        endpoint = 'lt/requests'))
    i18n_ReLMSmngmt = lazy_gettext(u'ReLMS Management')
    admin.add_view(RLMSPanel(db_session,       category = i18n_ReLMSmngmt, name = lazy_gettext(u"RLMS"),            endpoint = 'rlms/rlms'))
    admin.add_view(LaboratoryPanel(db_session, category = i18n_ReLMSmngmt, name = lazy_gettext(u"Registered labs"), endpoint = 'rlms/labs'))
    admin.add_view(UsersPanel(db_session,      category = lazy_gettext(u'Users'), name = lazy_gettext(u"Labmanager Users"), endpoint = 'users/labmanager'))
    admin.add_view(RedirectView('logout',      name = lazy_gettext(u"Log out"), endpoint = 'admin/logout'))
    admin.init_app(app)

