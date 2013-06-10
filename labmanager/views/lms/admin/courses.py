import sha
from sys import modules
from yaml import load as yload

from wtforms.fields import PasswordField

from flask import redirect, abort, url_for, request
from flask.ext import wtf
from flask.ext.login import current_user
from flask.ext.admin import expose, AdminIndexView

from labmanager.views.lms.admin import L4lLmsModelView
from labmanager.models import Permission
from labmanager.models import Course
from labmanager.database import db_session as DBS


class LmsCoursesPanel(L4lLmsModelView):

    column_list = ('name', 'context_id')

    form_columns = ('name', 'context_id')

    def __init__(self, session, **kwargs):
        super(LmsCoursesPanel, self).__init__(Course, session, **kwargs)

    def get_query(self, *args, **kwargs):
        query_obj = super(LmsCoursesPanel, self).get_query(*args, **kwargs)
        query_obj = query_obj.filter_by(lms = current_user.lms)
        return query_obj
        
