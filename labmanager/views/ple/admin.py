# -*-*- encoding: utf-8 -*-*-
#
# gateway4labs is free software: you can redistribute it and/or modify
# it under the terms of the BSD 2-Clause License
# gateway4labs is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.


import hashlib
import uuid
import traceback
import urlparse
import urllib2

from yaml import load as yload

from wtforms.fields import PasswordField

from flask import request, redirect, url_for, session, Markup, Response

from flask.ext import wtf
from flask.ext.admin import Admin, AdminIndexView, BaseView, expose
from flask.ext.admin.contrib.sqlamodel import ModelView
from flask.ext.login import current_user

from labmanager.scorm import get_scorm_object
from labmanager.models import LmsUser, Course, Laboratory, PermissionToLms, PermissionToLmsUser, PermissionToCourse
from labmanager.views import RedirectView, retrieve_courses

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
            return redirect(url_for('login_lms', next=request.url))

        return super(L4lPleModelView, self)._handle_view(name, **kwargs)

class L4lPleAdminIndexView(PleAuthManagerMixin, AdminIndexView):

    def _handle_view(self, name, **kwargs):
        if not self.is_accessible():
            return redirect(url_for('login_lms', next=request.url))

        return super(L4lPleAdminIndexView, self)._handle_view(name, **kwargs)

class L4lPleView(PleAuthManagerMixin, BaseView):
    def __init__(self, session, **kwargs):
        self.session = session
        super(L4lPleView, self).__init__(**kwargs)

    def _handle_view(self, name, **kwargs):
        if not self.is_accessible():
            return redirect(url_for('login_lms', next=request.url))

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

    column_list = ('login', 'full_name', 'access_level')

    form_columns = ('login', 'full_name', 'access_level', 'password')

    sel_choices = [(level, level.title()) for level in config['user_access_level']]

    form_overrides = dict(password=PasswordField, access_level=wtf.SelectField)
    form_args = dict( access_level=dict( choices=sel_choices ) )

    def __init__(self, session, **kwargs):
        super(PleUsersPanel, self).__init__(LmsUser, session, **kwargs)

    def get_query(self, *args, **kwargs):
        query_obj = super(PleUsersPanel, self).get_query(*args, **kwargs)
        query_obj = query_obj.filter_by(lms = current_user.lms)
        return query_obj

    def get_count_query(self, *args, **kwargs):
        query_obj = super(PleUsersPanel, self).get_count_query(*args, **kwargs)
        query_obj = query_obj.filter_by(lms = current_user.lms)
        return query_obj

        

    def on_model_change(self, form, model):
        # TODO: don't update password always
        model.lms   = current_user.lms
        model.password = hashlib.new('sha',model.password).hexdigest()


def create_lms_user_filter(session):
    def filter():
        return session.query(LmsUser).filter_by(lms = current_user.lms)

    return staticmethod(filter)

def create_permission_to_lms_filter(session):
    def filter():
        return session.query(PermissionToLms).filter_by(lms = current_user.lms)

    return staticmethod(filter)

def create_course_filter(session):
    def filter():
        return session.query(Course).filter_by(lms = current_user.lms)

    return staticmethod(filter)

###############################################
# 
#   Laboratories
# 

def local_id_formatter(v, c, laboratory, p):
    for permission in laboratory.lab_permissions:
        if permission.lms == current_user.lms:
            return permission.local_identifier
    return 'N/A'


class PleInstructorLaboratoriesPanel(L4lPleModelView):

    can_delete = False
    can_edit   = False
    can_create = False

    column_list = ('rlms', 'name', 'laboratory_id', 'local_identifier')

    column_formatters = dict( local_identifier = local_id_formatter )

    def __init__(self, session, **kwargs):
        super(PleInstructorLaboratoriesPanel, self).__init__(Laboratory, session, **kwargs)

    def get_query(self, *args, **kwargs):
        query_obj = super(PleInstructorLaboratoriesPanel, self).get_query(*args, **kwargs)
        query_obj = query_obj.join(PermissionToLms).filter_by(lms = current_user.lms)
        return query_obj

    def get_count_query(self, *args, **kwargs):
        query_obj = super(PleInstructorLaboratoriesPanel, self).get_count_query(*args, **kwargs)
        query_obj = query_obj.join(PermissionToLms).filter_by(lms = current_user.lms)
        return query_obj

    @expose('/scorm/scorm_<local_id>.zip')
    def get_scorm(self, local_id):
        db_lms = current_user.lms 

        if db_lms.basic_http_authentications:
            url = db_lms.basic_http_authentications[0].lms_url or ''
        else:
            url = ''

        lms_path = urlparse.urlparse(url).path or '/'
        extension = '/'
        if 'gateway4labs/' in lms_path:
            extension = lms_path[lms_path.rfind('gateway4labs/lms/list') + len('gateway4labs/lms/list'):]
            lms_path  = lms_path[:lms_path.rfind('gateway4labs/')]

        contents = get_scorm_object(False, local_id, lms_path, extension)
        return Response(contents, headers = {'Content-Type' : 'application/zip', 'Content-Disposition' : 'attachment; filename=scorm_%s.zip' % local_id})

#################################################
# 
#   Course management
# 

def format_space_url(v, c, space, p):
    shindig_url = space.lms.shindig_credentials[0]
    # shindig_space_url = '%s/rest/spaces/%s' % (shindig_url, space.context_id)
    # contents = urllib2.urlopen(shindig_space_url).read()
    # return json.loads(contents)['urls'][0]['value']
    return Markup('<a href="https://graasp.epfl.ch/#item=space_%s">link</a>' % space.context_id)

class PleSpacesPanel(L4lPleModelView):

    can_create = can_edit = False

    column_list = ('name', 'context_id', 'url')

    form_columns = ('name', 'context_id')

    column_formatters = dict( url = format_space_url  )

    def __init__(self, session, **kwargs):
        super(PleSpacesPanel, self).__init__(Course, session, **kwargs)

    def get_query(self, *args, **kwargs):
        query_obj = super(PleSpacesPanel, self).get_query(*args, **kwargs)
        query_obj = query_obj.filter_by(lms = current_user.lms)
        return query_obj

    def get_count_query(self, *args, **kwargs):
        query_obj = super(PleSpacesPanel, self).get_count_query(*args, **kwargs)
        query_obj = query_obj.filter_by(lms = current_user.lms)
        return query_obj

    def on_model_change(self, form, model):
        model.lms   = current_user.lms

class PlePermissionToSpacePanel(L4lPleModelView):

    form_args = dict(
        permission_to_lms = dict(query_factory = lambda : PlePermissionToSpacePanel.permission_to_lms_filter()),
        course = dict(query_factory = lambda : PlePermissionToSpacePanel.course_filter()),
    )


    def __init__(self, session, **kwargs):
        super(PlePermissionToSpacePanel, self).__init__(PermissionToCourse, session, **kwargs)
        PlePermissionToSpacePanel.permission_to_lms_filter = create_permission_to_lms_filter(self.session)
        PlePermissionToSpacePanel.course_filter = create_course_filter(self.session)

    def get_query(self, *args, **kwargs):
        query_obj = super(PlePermissionToSpacePanel, self).get_query(*args, **kwargs)
        query_obj = query_obj.join(Course).filter_by(lms = current_user.lms)
        return query_obj

    def get_count_query(self, *args, **kwargs):
        query_obj = super(PlePermissionToSpacePanel, self).get_count_query(*args, **kwargs)
        query_obj = query_obj.join(Course).filter_by(lms = current_user.lms)
        return query_obj

############################################## 
# 
#    Initialization
# 
def init_ple_admin(app, db_session):
    ple_admin_url = '/ple_admin'
    ple_admin = Admin(index_view = PleAdminPanel(url=ple_admin_url, endpoint = 'ple_admin'), name = u"PLE admin", url = ple_admin_url, endpoint = 'ple-admin')
    ple_admin.add_view(PleInstructorLaboratoriesPanel( db_session, name = u"Labs", endpoint = 'ple_admin_labs', url = 'labs'))
    ple_admin.add_view(PleSpacesPanel(db_session,    category = u"Spaces", name     = u"Spaces", endpoint = 'ple_admin_courses', url = 'spaces'))
    ple_admin.add_view(PlePermissionToSpacePanel(db_session,    category = u"Spaces", name     = u"Permissions", endpoint = 'ple_admin_course_permissions', url = 'spaces/permissions'))
    ple_admin.add_view(PleUsersPanel(db_session,      name     = u"Users", endpoint = 'ple_admin_users', url = 'users'))
    ple_admin.add_view(RedirectView('logout',         name = u"Log out", endpoint = 'ple_admin_logout', url = 'logout'))
    ple_admin.init_app(app)

