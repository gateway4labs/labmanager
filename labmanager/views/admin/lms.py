# -*-*- encoding: utf-8 -*-*-
from yaml import load as yload

from flask.ext import wtf
from flask.ext.login import current_user
from flask.ext.admin.model import InlineFormAdmin
from flask.ext.admin.contrib.sqlamodel import ModelView

from labmanager.models import Credential, NewLMS, NewCourse
from labmanager.views.admin import L4lModelView

config = yload(open('labmanager/config.yaml'))

class CredentialForm(InlineFormAdmin):
    form_columns = ('id','kind', 'key', 'secret')
    excluded_form_fields = ('id',)

    def postprocess_form(self, form):
        sel_choices =  [ (x , x.title()) for x in config['authentication_types']]
        form.kind = wtf.SelectField(u'Kind', choices=sel_choices)
        return form

class LMSPanel(L4lModelView):
    # los que se muestran en el index, son current_user.accessible_lmss()

    inline_models = (CredentialForm(Credential),)

    def __init__(self, session, **kwargs):
        super(LMSPanel, self).__init__(NewLMS, session, **kwargs)


class CoursePanel(L4lModelView):
    def __init__(self, session, **kwargs):
        super(CoursePanel, self).__init__(NewCourse, session, **kwargs)

