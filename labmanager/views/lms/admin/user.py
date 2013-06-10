import sha
from sys import modules
from yaml import load as yload

from wtforms.fields import PasswordField

from flask import redirect, abort, url_for, request
from flask.ext import wtf
from flask.ext.login import current_user
from flask.ext.admin import expose, AdminIndexView

from labmanager.views.lms.admin import L4lLmsModelView
from labmanager.models import LmsUser
from labmanager.database import db_session as DBS


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



