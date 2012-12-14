# -*-*- encoding: utf-8 -*-*-
from yaml import load as yload

from flask.ext import wtf
from flask.ext.login import current_user
from flask.ext.admin.model import InlineFormAdmin
from flask.ext.admin.contrib.sqlamodel import ModelView

from labmanager.models import Credential

config = yload(open('labmanager/config.yaml'))

class CredentialForm(InlineFormAdmin):
    form_columns = ('id','kind', 'key', 'secret')
    excluded_form_fields = ('id')

    def postprocess_form(self, form):
        sel_choices =  [ (x , x.title()) for x in config['authentication_types']]
        form.kind = wtf.SelectField(u'Kind', choices=sel_choices)
        return form

class LMSPanel(ModelView):
    category = 'LMS'
    name = 'LMS'
    inline_models = (CredentialForm(Credential),)

    def is_accessible(self):
        return current_user.is_authenticated()

class CoursePanel(ModelView):
    category = 'LMS'
    name = 'Courses'
    pass
