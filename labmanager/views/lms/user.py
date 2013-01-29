import sha
from sys import modules
from yaml import load as yload

from wtforms.fields import PasswordField

from flask import redirect, abort, url_for, request
from flask.ext import wtf
from flask.ext.login import current_user
from flask.ext.admin import expose, AdminIndexView

from labmanager.views.lms import L4lLmsModelView
from labmanager.models import Permission
from labmanager.models import LMSUser
from labmanager.database import db_session as DBS


class LmsUsersPanel(L4lLmsModelView):

    column_list = ('login', 'full_name')

    form_columns = ('login', 'full_name', 'password')

    form_overrides = dict(password=PasswordField)

    def __init__(self, session, **kwargs):
        super(LmsUsersPanel, self).__init__(LMSUser, session, **kwargs)

    def on_model_change(self, form, model):
        # TODO: don't update password always
        model.lms_id   = 1 # XXX TODO: retrieve from context of current user
        model.password = sha.new(model.password).hexdigest()



