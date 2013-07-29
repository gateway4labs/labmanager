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

#################################################################
# 
#            Base class
# 

class PleAuthManagerMixin(object):
    def is_accessible(self):
        if not current_user.is_authenticated():
            return False

        return session['usertype'] == 'lms'
    
class L4lPleInstructorModelView(PleAuthManagerMixin, ModelView):

    def _handle_view(self, name, **kwargs):
        if not self.is_accessible():
            return redirect(url_for('login_lms', next=request.url))

        return super(L4lPleInstructorModelView, self)._handle_view(name, **kwargs)

class L4lPleInstructorIndexView(PleAuthManagerMixin, AdminIndexView):

    def _handle_view(self, name, **kwargs):
        if not self.is_accessible():
            return redirect(url_for('login_lms', next=request.url))

        return super(L4lPleInstructorIndexView, self)._handle_view(name, **kwargs)

###############################################################
#
#              Index
# 

class LmsInstructorPanel(L4lPleInstructorIndexView):
    @expose()
    def index(self):
        return self.render("lms_admin/instructors.html")


###############################################################
#
#              Permissions for this user
#

from labmanager.models import PermissionToLmsUser

class PermissionToPleUserPanel(L4lPleInstructorModelView):

    can_create = can_edit = can_delete = False

    def __init__(self, session, **kwargs):
        super(PermissionToPleUserPanel, self).__init__(PermissionToLmsUser, session, **kwargs)

    def get_query(self, *args, **kwargs):
        query_obj = super(PermissionToPleUserPanel, self).get_query(*args, **kwargs)
        query_obj = query_obj.filter_by(lms_user = current_user)
        return query_obj

    def get_count_query(self, *args, **kwargs):
        query_obj = super(PermissionToPleUserPanel, self).get_count_query(*args, **kwargs)
        query_obj = query_obj.filter_by(lms_user = current_user)
        return query_obj


#####################################################################
# 
#              Initialization
# 

def init_instructor_admin(app, db_session):
    ple_instructor_url = '/ple_instructor'
    ple_instructor = Admin(index_view = PleInstructorPanel(url=ple_instructor_url, endpoint = 'ple_instructor'), name = u"PLE instructor", url = ple_instructor_url, endpoint = 'ple-instructor')
    ple_instructor.add_view(PermissionToPleUserPanel(db_session, name     = u"Permissions", endpoint = 'ple_instructor_permissions', url = 'permissions'))
    ple_instructor.add_view(RedirectView('logout',         name = u"Log out", endpoint = 'ple_instructor_logout', url = 'logout'))
    ple_instructor.init_app(app)

