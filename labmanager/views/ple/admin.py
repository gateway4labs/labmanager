# -*-*- encoding: utf-8 -*-*-
#
# gateway4labs is free software: you can redistribute it and/or modify
# it under the terms of the BSD 2-Clause License
# gateway4labs is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

import json
import hashlib
import uuid
import traceback
import urlparse
import urllib2

from yaml import load as yload

from wtforms.fields import PasswordField

from flask.ext.wtf import Form, validators, TextField

from flask import request, redirect, url_for, session, Markup, Response

from flask.ext import wtf
from flask.ext.admin import Admin, AdminIndexView, BaseView, expose
from flask.ext.admin.contrib.sqlamodel import ModelView
from flask.ext.login import current_user
from flask.ext.babel import gettext, ngettext, lazy_gettext

from labmanager.scorm import get_scorm_object
from labmanager.models import LtUser, Course, Laboratory, PermissionToLt, PermissionToLtUser, PermissionToCourse, RequestPermissionLT
from labmanager.views import RedirectView, retrieve_courses
from labmanager.db import db_session
from labmanager.rlms import get_manager_class

from sqlalchemy import func
 

config = yload(open('labmanager/config/config.yml'))


#################################################################
# 
#            Base class
# 

class PleAuthManagerMixin(object):
    def is_accessible(self):
        if not current_user.is_authenticated():
            return False

        return session['usertype'] == 'lms' and current_user.access_level == 'admin'
    
class L4lPleModelView(PleAuthManagerMixin, ModelView):

    def _handle_view(self, name, **kwargs):
        if not self.is_accessible():
# IRENE    return redirect(url_for('login_lms', next=request.url))    
            return redirect(url_for('login_ple', next=request.url))

        return super(L4lPleModelView, self)._handle_view(name, **kwargs)

class L4lPleAdminIndexView(PleAuthManagerMixin, AdminIndexView):

    def _handle_view(self, name, **kwargs):
        if not self.is_accessible():   
# IRENE     return redirect(url_for('login_lms', next=request.url))         
            return redirect(url_for('login_ple', next=request.url))

        return super(L4lPleAdminIndexView, self)._handle_view(name, **kwargs)

class L4lPleView(PleAuthManagerMixin, BaseView):
    def __init__(self, session, **kwargs):
        self.session = session
        super(L4lPleView, self).__init__(**kwargs)

    def _handle_view(self, name, **kwargs):
        if not self.is_accessible():
# IRENE     return redirect(url_for('login_lms', next=request.url))      
            return redirect(url_for('login_ple', next=request.url))

        return super(L4lPleView, self)._handle_view(name, **kwargs)


##############################################
# 
#    Index
# 


class PleAdminPanel(L4lPleAdminIndexView):
    @expose()
    def index(self):
        return self.render("ple_admin/index.html")


###############################################
# 
#   User management
# 

class PleUsersPanel(L4lPleModelView):

    can_delete = True
    can_edit   = False
    can_create = True
    column_list = ('login', 'full_name', 'access_level')
    form_columns = ('login','full_name', 'access_level', 'password')
    
    column_labels = dict(login = lazy_gettext('login'),
                                    full_name = lazy_gettext('full_name'),
                                    access_level = lazy_gettext('access_level'),
                                    password = lazy_gettext('password'))

    sel_choices = [(level, level.title()) for level in config['user_access_level']]

    form_overrides = dict(password=PasswordField, access_level=wtf.SelectField)
    form_args = dict( access_level=dict( choices=sel_choices ) )

    def __init__(self, session, **kwargs):
        super(PleUsersPanel, self).__init__(LtUser, session, **kwargs)

    def get_query(self, *args, **kwargs):
        query_obj = super(PleUsersPanel, self).get_query(*args, **kwargs)
        query_obj = query_obj.filter_by(lt = current_user.lt)
        return query_obj

    def get_count_query(self, *args, **kwargs):
        query_obj = super(PleUsersPanel, self).get_count_query(*args, **kwargs)
        query_obj = query_obj.filter_by(lt = current_user.lt)
        return query_obj

        

    def on_model_change(self, form, model):
        # TODO: don't update password always
        model.lt   = current_user.lt
        model.password = hashlib.new('sha',model.password).hexdigest()


def create_permission_to_lms_filter(session):
    def filter():
        return session.query(PermissionToLt).filter_by(lt = current_user.lt)

    return staticmethod(filter)

def create_course_filter(session):
    def filter():
        return session.query(Course).filter_by(lt = current_user.lt)

    return staticmethod(filter)

###############################################
# 
#   Laboratories
# 

def local_id_formatter(v, c, laboratory, p):
    for permission in laboratory.lab_permissions:
        if permission.lt == current_user.lt:
            return permission.local_identifier
    return gettext('N/A')

def list_widgets_formatter(v, c, laboratory, p):
    return Markup('<a href="%s"> gettext("list")</a>' % url_for('.list_widgets', local_identifier = local_id_formatter(v, c, laboratory, p)))



def accessibility_formatter(v, c, lab, p):
    
    mylt = current_user.lt
    permission = db_session.query(PermissionToLt).filter_by(lt = mylt, laboratory = lab).first()

    if not permission:
        return gettext(u"Invalid permission")

    if permission.accessible:
        currently = gettext('This lab IS accesible')
        labaccessible = gettext('false')
        klass = 'btn-danger'
        msg = gettext('Make not accessible')
    else:
        currently = gettext(u'This lab is NOT accesible')
        labaccessible = gettext('true')
        klass = 'btn-success'
        msg = gettext('Make accessible')

                                       
    return Markup("""<form method='POST' action='%(url)s' style="text-align: center">
                        %(currently)s <BR>
                        <input type='hidden' name='accessible_value' value='%(accessible_value)s'/>
                        <input type='hidden' name='permission_to_lt_id' value='%(permission_id)s'/>
                        <input class='btn %(klass)s' type='submit' value="%(msg)s"></input>
                    </form>""" % dict(
                        url                      = url_for('.change_accessibility'),                     
                        accessible_value         = labaccessible,
                        permission_id            = permission.id,
                        klass                    = klass,
                        msg                      = msg,
                        currently                = currently,
                    ))


def request_formatter(v, c, lab, p):
    
    mylt = current_user.lt
    
    

    laboratory_available = db_session.query(Laboratory).filter_by(available = '1', id = lab.id).first()

    permission = db_session.query(PermissionToLt).filter_by(lt = mylt, laboratory = laboratory_available).first()
    
    request = db_session.query(RequestPermissionLT).filter_by(lt = mylt, laboratory = laboratory_available).first()
    
    
    # if there is not a pending request ...
    if not request:

        if not permission:
            currently = gettext(u'Available for request')
            lab_request = gettext(u'true')
            klass = 'btn-success'
            msg = gettext(u'Request laboratory')
            permission_to_lt_id = ''
            lab_id = lab.id

        else:
            currently = gettext(u'Ready to use')
            lab_request = gettext(u'false')
            klass = 'btn-danger'
            msg = gettext(u'Delete laboratory')
            permission_to_lt_id = permission.id
            lab_id = lab.id
                
                   
        return Markup("""<form method='POST' action='%(url)s' style="text-align: center">
                        %(currently)s <BR> 
                        <input type='hidden' name='lab_request' value='%(lab_request)s'/>
                        <input type='hidden' name='permission_to_lt_id' value='%(permission_to_lt_id)s'/>
                        <input type='hidden' name='lab_id' value='%(lab_id)s'/>
                        <input class='btn %(klass)s' type='submit' value="%(msg)s"></input>
                    </form>""" % dict(
                        url                      = url_for('.lab_request'),                     
                        lab_request              = lab_request,
                        permission_to_lt_id     = permission_to_lt_id,
                        klass                    = klass,
                        msg                      = msg,
                        currently                = currently,
                        lab_id                   = lab_id,
                    ))

    else: # if there is a pending request, offer the possibility to cancel such request, or wait until the labmanager admin processes it.

        currently = gettext(u'Access request pending')
        klass = 'btn-danger'
        msg = gettext(u'Delete access request')
        
                
        return Markup("""<form method='POST' action='%(url)s' style="text-align: center">
                        %(currently)s <BR> 
                        <input type='hidden' name='request_id' value='%(request_id)s'/>
                        <input class='btn %(klass)s' type='submit' value="%(msg)s"></input>
                    </form>""" % dict(
                        url                      = url_for('.cancel_lab_request'),                     
                        currently                = currently,
                        request_id               = request.id,
                        klass                    = klass,
                        msg                      = msg,    
                    ))


        


class PleInstructorLaboratoriesPanel(L4lPleModelView):

    can_delete = False
    can_edit   = False
    can_create = False

    column_list = ('rlms', 'name', 'laboratory_id', 'local_identifier', 'widgets', 'accessible')
    column_formatters = dict( local_identifier = local_id_formatter, widgets = list_widgets_formatter, accessible = accessibility_formatter )
    column_labels = dict(rlms = lazy_gettext('rlms'),
                                    name = lazy_gettext('name'),
                                    laboratory_id = lazy_gettext('laboratory_id'),
                                    local_identifier = lazy_gettext('local_identifier'),
                                    widgets = lazy_gettext('widgets'),
                                    accessible = lazy_gettext('accesible'))
                                    
    column_descriptions = dict( accessible = gettext("Make this laboratory automatically accessible by any Graasp space belonging to the institution represented by this Learning Tool"))

    def __init__(self, session, **kwargs):
        super(PleInstructorLaboratoriesPanel, self).__init__(Laboratory, session, **kwargs)

    def get_query(self, *args, **kwargs):
        query_obj = super(PleInstructorLaboratoriesPanel, self).get_query(*args, **kwargs)
        query_obj = query_obj.join(PermissionToLt).filter_by(lt = current_user.lt)
        return query_obj

    def get_count_query(self, *args, **kwargs):
        query_obj = super(PleInstructorLaboratoriesPanel, self).get_count_query(*args, **kwargs)
        query_obj = query_obj.join(PermissionToLt).filter_by(lt = current_user.lt)
        return query_obj

    @expose("/widgets/<local_identifier>/")
    def list_widgets(self, local_identifier):
        laboratory = self.session.query(Laboratory).join(PermissionToLt).filter_by(lt = current_user.lt, local_identifier = local_identifier).first()
        if laboratory is None:
            return self.render("ple_admin/errors.html", message = gettext("Laboratory not found"))

        rlms_db = laboratory.rlms
        RLMS_CLASS = get_manager_class(rlms_db.kind, rlms_db.version)
        rlms = RLMS_CLASS(rlms_db.configuration)

        widgets = rlms.list_widgets(laboratory.laboratory_id)
        return self.render("ple_admin/list_widgets.html", widgets = widgets, institution_id = current_user.lt.name, lab_name = local_identifier)



    @expose('/lab', methods = ['POST'])
    def change_accessibility(self):
        isaccessible = unicode(request.form['accessible_value']).lower() == 'true'

        lt = current_user.lt

        permission_id = int(request.form['permission_to_lt_id'])
        permission = self.session.query(PermissionToLt).filter_by(id = permission_id, lt = lt).first()

        if permission:
            permission.accessible = isaccessible
            self.session.commit()
     
        return redirect(url_for('.index_view'))

class PleInstructorRequestLaboratoriesPanel(L4lPleModelView):

    can_delete = False
    can_edit   = False
    can_create = False

    column_list = ('rlms', 'name', 'laboratory_id', 'request_access')


    column_formatters = dict(request_access = request_formatter)

    column_descriptions = dict( request_access = "Request access to a lab. The Labmanager admin must accept or deny your request.")
   
    def __init__(self, session, **kwargs):
        super(PleInstructorRequestLaboratoriesPanel, self).__init__(Laboratory, session, **kwargs)

    def get_query(self, *args, **kwargs):
        query_obj = super(PleInstructorRequestLaboratoriesPanel, self).get_query(*args, **kwargs)
        #laboratories_query = self.session.query(Laboratory).filter_by(available = '1')
        
        query_obj = query_obj.filter_by(available = '1')
         
        # laboratories_query = self.session.query(Laboratory).filter_by(available = '1').join(PermissionToLt).filter_by(lt = current_user.lt)

        return query_obj

    def get_count_query(self, *args, **kwargs):
        query_obj = super(PleInstructorRequestLaboratoriesPanel, self).get_count_query(*args, **kwargs)
        query_obj = query_obj.filter_by(available = '1')
        return query_obj
	
    @expose('/lab_request', methods = ['GET','POST'])
    def lab_request(self):

        lab_request = unicode(request.form['lab_request']).lower() == 'true'

        # if lab_request == true, then request the creation of permission. Else, delete the permission over this lab for this lt (no need to ask the labmanager admin to do this).   
        if lab_request:
                   
            lab_id = unicode(request.form['lab_id'])
            lab = self.session.query(Laboratory).filter_by(id = lab_id).first()
            
            request_perm = RequestPermissionLT(lt = current_user.lt, laboratory = lab, local_identifier = lab.default_local_identifier)

            self.session.add(request_perm)    

        else:
            
            permission_id = unicode(request.form['permission_to_lt_id'])
            
            permission = self.session.query(PermissionToLt).filter_by(id = permission_id).first()
            
            self.session.delete(permission)    

        self.session.commit()
            
        return redirect(url_for('.index_view'))

       

    @expose('/cancel_lab_request', methods = ['GET','POST'])
    def cancel_lab_request(self):

        req_id = unicode(request.form['request_id'])
        req = self.session.query(RequestPermissionLT).filter_by(id = req_id).first()
            
        self.session.delete(req)    

        self.session.commit()
            
        return redirect(url_for('.index_view'))

       


#################################################
# 
#   Course management
# 

def format_space_url(v, c, space, p):
    shindig_url = space.lt.shindig_credentials[0]
    # shindig_space_url = '%s/rest/spaces/%s' % (shindig_url, space.context_id)
    # contents = urllib2.urlopen(shindig_space_url).read()
    # return json.loads(contents)['urls'][0]['value']
    return Markup('<a target="_blank" href="https://graasp.epfl.ch/#item=space_%s">link</a>' % space.context_id)

class PleSpacesPanel(L4lPleModelView):

    can_create = can_edit = False

    column_list = ('name', 'context_id', 'url')
    form_columns = ('name', 'context_id')
    column_formatters = dict( url = format_space_url  )
    column_labels = dict(name = lazy_gettext('name'),
                                    context_id = lazy_gettext('context_id'),
                                    url = lazy_gettext('url'))
                                    
    def __init__(self, session, **kwargs):
        super(PleSpacesPanel, self).__init__(Course, session, **kwargs)

    def get_query(self, *args, **kwargs):
        query_obj = super(PleSpacesPanel, self).get_query(*args, **kwargs)
        query_obj = query_obj.filter_by(lt = current_user.lt)
        return query_obj

    def get_count_query(self, *args, **kwargs):
        query_obj = super(PleSpacesPanel, self).get_count_query(*args, **kwargs)
        query_obj = query_obj.filter_by(lt = current_user.lt)
        return query_obj

    def on_model_change(self, form, model):
        model.lt   = current_user.lt

class SpaceUrlForm(Form):

    url = TextField(lazy_gettext('Space URL'), [validators.Length(min=6, max=200),
                        validators.URL()], description = lazy_gettext("Drop here the URL of the Space."), default = "http://graasp.epfl.ch/#item=space_1234")

def retrieve_space_name(numeric_identifier):
    # Retrieve the space name from Shindig
    shindig_url = current_user.lt.shindig_credentials[0].shindig_url
    shindig_space_url = '%s/rest/spaces/%s' % (shindig_url, numeric_identifier)
    shindig_space_contents_json = urllib2.urlopen(shindig_space_url).read()
    shindig_space_contents = json.loads(shindig_space_contents_json)
    space_name = shindig_space_contents.get('entry', {}).get('displayName')
    return space_name


def create_new_space(numeric_identifier, space_name):
    # Create the space
    context_id = unicode(numeric_identifier)
    course = Course(name = space_name, lt = current_user.lt, context_id = context_id)

    # Add it to the database
    db_session.add(course)
    return course

def parse_space_url(url):
    """ Given a Graasp URL, retrieve the space identifier (a number) """

    # This is done in a different way if the space url ends with a number (the url contains space_) or if the url ends with a text (the url contains  url=)
    if 'space_' in url:
        try:
            context_id = int(url.split('space_')[1])
        except:
            raise Exception(gettext("Invalid format. Expected space_NUMBER"))
        else:
            return context_id

    elif 'url=' in url:
        try:
            space_name = url.split('url=')[1]
            json_file = 'http://graasp.epfl.ch/item3a/' + space_name + '.json'
            json_response = urllib2.urlopen(json_file)
            contents=json.loads(json_response.read())
            
            context_id=contents['id']

            return context_id

        except:
            raise Exception(gettext("Invalid format. Expected a valid Graasp space URL"))

    raise Exception(gettext("Invalid format. Expected http://graasp.epfl.ch/#item=space_SOMETHING"))
   

class PleNewSpacesPanel(L4lPleView):

    @expose(methods = ['GET', 'POST'])
    def index(self):
        form = SpaceUrlForm()

        permissions = current_user.lt.lab_permissions
        lab_ids = dict([ 
                (permission.local_identifier, { 
                            'name' : permission.laboratory.name, 
                            'checked' : request.form.get('lab_%s' % permission.local_identifier, 'off') in ('checked', 'on')
                        }) 
                for permission in permissions ])

        request_space_name = False

        if form.validate_on_submit():
            try:
                context_id = parse_space_url(form.url.data)
            except Exception as e:
                form.url.errors.append(e.message)
            else:
                existing_course = self.session.query(Course).filter_by(lt = current_user.lt, context_id = context_id).first()
                if existing_course:
                    form.url.errors.append(gettext(u"Space already registered"))
                else:
                    space_name = retrieve_space_name(context_id)
                    # If space_name can not be retrieved (e.g., a closed or hidden space)
                    if not space_name:
                        # Try to get it from the form.
                        space_name = request.form.get('space_name')

                    # If it was possible, add the new space
                    if space_name:
                        course = create_new_space(context_id, space_name or gettext('Invalid name'))

                        labs_to_grant = [ lab_id for lab_id in lab_ids if lab_ids[lab_id]['checked'] ]

                        for lab_to_grant in labs_to_grant:
                            permission = [ permission for permission in permissions if permission.local_identifier == lab_to_grant ][0]
                            permission_to_course = PermissionToCourse(course = course, permission_to_lt = permission)
                            db_session.add(permission_to_course)

                        db_session.commit()

                        return redirect(url_for('ple_admin_courses.index_view'))

                    # But if it was not possible to add it, add a new field called space_name
                    else:
                        request_space_name = True

        return self.render("ple_admin/new_space.html", form = form, lab_ids = lab_ids, request_space_name = request_space_name)

class PlePermissionToSpacePanel(L4lPleModelView):

    form_args = dict(
        permission_to_lt = dict(query_factory = lambda : PlePermissionToSpacePanel.permission_to_lms_filter()),
        course = dict(query_factory = lambda : PlePermissionToSpacePanel.course_filter()),
    )

    column_labels = dict(
        permission_to_lt = lazy_gettext('Permission'),
        course = lazy_gettext('Space'),
    )


    def __init__(self, session, **kwargs):
        super(PlePermissionToSpacePanel, self).__init__(PermissionToCourse, session, **kwargs)
        PlePermissionToSpacePanel.permission_to_lms_filter = create_permission_to_lms_filter(self.session)
        PlePermissionToSpacePanel.course_filter = create_course_filter(self.session)

    def get_query(self, *args, **kwargs):
        query_obj = super(PlePermissionToSpacePanel, self).get_query(*args, **kwargs)
        query_obj = query_obj.join(Course).filter_by(lt = current_user.lt)
        return query_obj

    def get_count_query(self, *args, **kwargs):
        query_obj = super(PlePermissionToSpacePanel, self).get_count_query(*args, **kwargs)
        query_obj = query_obj.join(Course).filter_by(lt = current_user.lt)
        return query_obj

############################################## 
# 
#    Initialization
# 
def init_ple_admin(app, db_session):
    ple_admin_url = '/ple_admin'
    ple_admin = Admin(index_view = PleAdminPanel(url=ple_admin_url, endpoint = 'ple_admin'), name = lazy_gettext(u'PLE admin'), url = ple_admin_url, endpoint = 'ple-admin')
    ple_admin.add_view(PleInstructorLaboratoriesPanel( db_session,  category = lazy_gettext(u"Labs"), name = lazy_gettext(u"Available labs"), endpoint = 'ple_admin_labs', url = 'labs/available'))
    i18n_spaces = lazy_gettext(u'Spaces')
    ple_admin.add_view(PleNewSpacesPanel(db_session,             category = i18n_spaces, name     = lazy_gettext(u'New'), endpoint = 'ple_admin_new_courses', url = 'spaces/create'))
    ple_admin.add_view(PleSpacesPanel(db_session,                   category = i18n_spaces, name     = lazy_gettext(u'Spaces'), endpoint = 'ple_admin_courses', url = 'spaces'))
    ple_admin.add_view(PlePermissionToSpacePanel(db_session,  category = i18n_spaces, name     = lazy_gettext(u'Permissions'), endpoint = 'ple_admin_course_permissions', url = 'spaces/permissions'))
    ple_admin.add_view(PleUsersPanel(db_session,      name = lazy_gettext(u'Users'), endpoint = 'ple_admin_users', url = 'users'))
    ple_admin.add_view(RedirectView('logout',         name = lazy_gettext(u'Log out'), endpoint = 'ple_admin_logout', url = 'logout'))
    ple_admin.init_app(app)

    # Uncomment for debugging purposes
    # app.config['TRAP_BAD_REQUEST_ERRORS'] = True