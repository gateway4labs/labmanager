# -*-*- encoding: utf-8 -*-*-
#
# lms4labs is free software: you can redistribute it and/or modify
# it under the terms of the BSD 2-Clause License
# lms4labs is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.


from flask import request, redirect, url_for, session

from flask.ext.admin import Admin, AdminIndexView
from flask.ext.admin.contrib.sqlamodel import ModelView
from flask.ext.login import current_user

#################################################################
# 
#            Base class
# 

class LmsAuthManagerMixin(object):
    def is_accessible(self):
        if not current_user.is_authenticated():
            return False

        return session['usertype'] == 'lms' and current_user.access_level == 'admin'
    
class L4lLmsModelView(LmsAuthManagerMixin, ModelView):

    def _handle_view(self, name, **kwargs):
        if not self.is_accessible():
            return redirect(url_for('login_lms', next=request.url))

        return super(L4lLmsModelView, self)._handle_view(name, **kwargs)

class L4lLmsAdminIndexView(LmsAuthManagerMixin, AdminIndexView):

    def _handle_view(self, name, **kwargs):
        if not self.is_accessible():
            return redirect(url_for('login_lms', next=request.url))

        return super(L4lLmsAdminIndexView, self)._handle_view(name, **kwargs)


def init_lms_admin(app, db_session):
    from labmanager.admin import RedirectView

    from .main import LmsAdminPanel
    from .user import LmsUsersPanel
    from .courses import LmsCoursesPanel

    lms_admin_url = '/lms_admin'
    lms_admin = Admin(index_view = LmsAdminPanel(url=lms_admin_url, endpoint = 'lms-admin'), name = u"LMS admin", url = lms_admin_url, endpoint = lms_admin_url)
    lms_admin.add_view(LmsCoursesPanel(db_session,    name     = u"Courses", endpoint = 'mylms/courses'))
    lms_admin.add_view(LmsUsersPanel(db_session,      name     = u"Users", endpoint = 'mylms/users'))
    lms_admin.add_view(RedirectView('logout',         name = u"Log out", endpoint = 'mylms/logout'))
    lms_admin.init_app(app)

