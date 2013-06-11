# -*-*- encoding: utf-8 -*-*-

from flask import request, redirect, url_for, session
from flask.ext.login import current_user
from flask.ext.admin import Admin, BaseView, AdminIndexView
from flask.ext.admin.contrib.sqlamodel import ModelView

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


def init_admin(app, db_session):
    from .lms  import LMSPanel, CoursePanel
    from .rlms import RLMSPanel, LaboratoryPanel, PermissionPanel, PermissionToLmsPanel
    from .main import AdminPanel, UsersPanel, LmsUsersPanel
    from labmanager.admin import RedirectView

    admin_url = '/admin'

    admin = Admin(index_view = AdminPanel(url=admin_url), name = u"Lab Manager", url = admin_url, endpoint = admin_url)

    admin.add_view(PermissionPanel(db_session,             category = u"Permissions", name = u"Course permissions", endpoint = 'permissions/course'))
    admin.add_view(PermissionToLmsPanel(db_session, category = u"Permissions", name = u"LMS permissions",    endpoint = 'permissions/lms'))

    admin.add_view(LMSPanel(db_session,        category = u"LMS Management", name = u"LMS",     endpoint = 'lms/lms'))
    admin.add_view(CoursePanel(db_session,     category = u"LMS Management", name = u"Courses", endpoint = 'lms/courses'))

    admin.add_view(RLMSPanel(db_session,       category = u"ReLMS Management", name = u"RLMS",            endpoint = 'rlms/rlms'))
    admin.add_view(LaboratoryPanel(db_session, category = u"ReLMS Management", name = u"Registered labs", endpoint = 'rlms/labs'))

    admin.add_view(UsersPanel(db_session,      category = u"Users", name = u"Labmanager Users", endpoint = 'users/labmanager'))
    admin.add_view(LmsUsersPanel(db_session,   category = u"Users", name = u"LMS Users",        endpoint = 'users/lms'))

    admin.add_view(RedirectView('logout',      name = u"Log out", endpoint = 'admin/logout'))

    admin.init_app(app)

