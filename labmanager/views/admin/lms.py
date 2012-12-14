# -*-*- encoding: utf-8 -*-*-
from yaml import load as yload

from flask.ext import wtf
from flask.ext.login import current_user
from flask.ext.admin.model import InlineFormAdmin
from flask.ext.admin.contrib.sqlamodel import ModelView

from labmanager.models import Credential, NewLMS, NewCourse

config = yload(open('labmanager/config.yaml'))

class CredentialForm(InlineFormAdmin):
    form_columns = ('id','kind', 'key', 'secret')
    excluded_form_fields = ('id')

    def postprocess_form(self, form):
        sel_choices =  [ (x , x.title()) for x in config['authentication_types']]
        form.kind = wtf.SelectField(u'Kind', choices=sel_choices)
        return form

class LMSPanel(ModelView):
    # los que se muestran en el index, son current_user.accessible_lmss()

    def __init__(self, session, **kwargs):
        # You can pass name and other parameters if you want to
        default_args = { "category":u"LMS", "name":u"LMS" }
        default_args.update(**kwargs)
        super(LMSPanel, self).__init__(NewLMS, session, **default_args)

    inline_models = (CredentialForm(Credential),)

    def is_accessible(self):
        return current_user.is_authenticated()

class CoursePanel(ModelView):
    def __init__(self, session, **kwargs):
        # You can pass name and other parameters if you want to
        default_args = { "category":u"LMS", "name":u"Courses" }
        default_args.update(**kwargs)
        super(CoursePanel, self).__init__(NewCourse, session, **default_args)

