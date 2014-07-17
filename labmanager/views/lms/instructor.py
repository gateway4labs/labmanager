# -*-*- encoding: utf-8 -*-*-
#
# gateway4labs is free software: you can redistribute it and/or modify
# it under the terms of the BSD 2-Clause License
# gateway4labs is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

from flask import request, redirect, url_for, session
from flask.ext.admin import Admin, AdminIndexView, expose
from flask.ext.admin.contrib.sqlamodel import ModelView
from flask.ext.login import current_user
from labmanager.views import RedirectView
from labmanager.babel import lazy_gettext
from labmanager.db import db

#################################################################
# 
#            Base class
# 

class LmsAuthManagerMixin(object):
    def is_accessible(self):
        if not current_user.is_authenticated():
            return False
        return session['usertype'] == 'lms' and current_user.access_level == 'instructor'
    
class L4lLmsInstructorModelView(LmsAuthManagerMixin, ModelView):
    def _handle_view(self, name, **kwargs):
        if not self.is_accessible():
            return redirect(url_for('login_lms', next=request.url))
        return super(L4lLmsInstructorModelView, self)._handle_view(name, **kwargs)

class L4lLmsInstructorIndexView(LmsAuthManagerMixin, AdminIndexView):
    def _handle_view(self, name, **kwargs):
        if not self.is_accessible():
            return redirect(url_for('login_lms', next=request.url))
        return super(L4lLmsInstructorIndexView, self)._handle_view(name, **kwargs)

###############################################################
#
#              Index
# 

class LmsInstructorPanel(L4lLmsInstructorIndexView):
    @expose()
    def index(self):
        return self.render("lms_admin/instructors.html")

###############################################################
#
#              Permissions for this user
#

from labmanager.models import PermissionToLtUser

class PermissionToLmsUserPanel(L4lLmsInstructorModelView):

    can_create = can_edit = can_delete = False
    column_labels = dict(permission_to_lms = lazy_gettext('Permission To LMS'),
                                    lms_user = lazy_gettext('LMS User'),
                                    key = lazy_gettext('Key'),
                                    secret = lazy_gettext('Secret'))  
                                    
    def __init__(self, session, **kwargs):
        super(PermissionToLmsUserPanel, self).__init__(PermissionToLtUser, session, **kwargs)

    def get_query(self, *args, **kwargs):
        query_obj = super(PermissionToLmsUserPanel, self).get_query(*args, **kwargs)
        query_obj = query_obj.filter_by(lt_user = current_user)
        return query_obj

    def get_count_query(self, *args, **kwargs):
        query_obj = super(PermissionToLmsUserPanel, self).get_count_query(*args, **kwargs)
        query_obj = query_obj.filter_by(lt_user = current_user)
        return query_obj

#####################################################################
# 
#              Initialization
# 

def init_instructor_admin(app):
    lms_instructor_url = '/lms_instructor'
    lms_instructor = Admin(index_view = LmsInstructorPanel(url=lms_instructor_url, endpoint = 'lms_instructor'), name = lazy_gettext(u'LMS instructor'), url = lms_instructor_url, endpoint = 'lms-instructor')
    lms_instructor.add_view(PermissionToLmsUserPanel(db.session, name     = lazy_gettext(u'Permissions'), endpoint = 'lms_instructor_permissions', url = 'permissions'))
    lms_instructor.add_view(RedirectView('logout',         name = lazy_gettext(u'Log out'), endpoint = 'lms_instructor_logout', url = 'logout'))
    lms_instructor.init_app(app)
