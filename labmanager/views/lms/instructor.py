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

        return session['usertype'] == 'lms'
    
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
    pass

#####################################################################
# 
#              Initialization
# 

def init_instructor_admin(app, db_session):
    from labmanager.admin import RedirectView

    lms_instructor_url = '/lms_instructor'
    lms_instructor = Admin(index_view = LmsInstructorPanel(url=lms_instructor_url, endpoint = 'lms-instructor'), name = u"LMS instructor", url = lms_instructor_url, endpoint = lms_instructor_url)
    lms_instructor.add_view(RedirectView('logout',         name = u"Log out", endpoint = 'mycourses/logout'))
    lms_instructor.init_app(app)

