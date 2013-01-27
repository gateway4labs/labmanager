# -*-*- encoding: utf-8 -*-*-
import sha
import threading

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

    column_list = ('name', 'url')
    inline_models = (CredentialForm(Credential),)

    def __init__(self, session, **kwargs):
        super(LMSPanel, self).__init__(NewLMS, session, **kwargs)
        self.local_data = threading.local()

    def edit_form(self, obj = None):
        form = super(LMSPanel, self).edit_form(obj)
        self.local_data.authentications = {}
        if obj is not None:
            for auth in obj.authentications:
                self.local_data.authentications[auth.id] = auth.secret
        return form

    def on_model_change(self, form, model):
        old_authentications = getattr(self.local_data, 'authentications', {})

        for authentication in model.authentications:
            if authentication.kind == 'basic':
                # If it's the same secret, don't change it
                old_secret = old_authentications.get(authentication.id, None)
                if authentication.secret == old_secret:
                    continue
                # Otherwise, regenerate the hash
                hash_password = sha.new(authentication.secret).hexdigest()
                authentication.secret = hash_password 
            

class CoursePanel(L4lModelView):
    def __init__(self, session, **kwargs):
        super(CoursePanel, self).__init__(NewCourse, session, **kwargs)

