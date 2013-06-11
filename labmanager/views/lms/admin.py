# -*-*- encoding: utf-8 -*-*-
#
# lms4labs is free software: you can redistribute it and/or modify
# it under the terms of the BSD 2-Clause License
# lms4labs is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.


import sha

from wtforms.fields import PasswordField

from flask import request, redirect, url_for, session

from flask.ext.admin import Admin, AdminIndexView
from flask.ext.admin.contrib.sqlamodel import ModelView
from flask.ext.login import current_user

from labmanager.models import LmsUser, Course

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


##############################################
# 
#    Index
# 


class LmsAdminPanel(L4lLmsAdminIndexView):
    pass



###############################################
# 
#   User management
# 

class LmsUsersPanel(L4lLmsModelView):

    column_list = ('login', 'full_name', 'access_level')

    form_columns = ('login', 'full_name', 'access_level', 'password')

    form_overrides = dict(password=PasswordField)

    def __init__(self, session, **kwargs):
        super(LmsUsersPanel, self).__init__(LmsUser, session, **kwargs)

    def get_query(self, *args, **kwargs):
        query_obj = super(LmsUsersPanel, self).get_query(*args, **kwargs)
        query_obj = query_obj.filter_by(lms = current_user.lms)
        return query_obj
        

    def on_model_change(self, form, model):
        # TODO: don't update password always
        model.lms   = current_user.lms
        model.password = sha.new(model.password).hexdigest()


#################################################
# 
#   Course management
# 

class LmsCoursesPanel(L4lLmsModelView):

    column_list = ('name', 'context_id')

    form_columns = ('name', 'context_id')

    def __init__(self, session, **kwargs):
        super(LmsCoursesPanel, self).__init__(Course, session, **kwargs)

    def get_query(self, *args, **kwargs):
        query_obj = super(LmsCoursesPanel, self).get_query(*args, **kwargs)
        query_obj = query_obj.filter_by(lms = current_user.lms)
        return query_obj


############################################## 
# 
#    Initialization
# 
def init_lms_admin(app, db_session):
    from labmanager.admin import RedirectView

    lms_admin_url = '/lms_admin'
    lms_admin = Admin(index_view = LmsAdminPanel(url=lms_admin_url, endpoint = 'lms-admin'), name = u"LMS admin", url = lms_admin_url, endpoint = lms_admin_url)
    lms_admin.add_view(LmsCoursesPanel(db_session,    name     = u"Courses", endpoint = 'mylms/courses'))
    lms_admin.add_view(LmsUsersPanel(db_session,      name     = u"Users", endpoint = 'mylms/users'))
    lms_admin.add_view(RedirectView('logout',         name = u"Log out", endpoint = 'mylms/logout'))
    lms_admin.init_app(app)

