# -*-*- encoding: utf-8 -*-*-
import sha
import threading

from yaml import load as yload

from flask import Markup, url_for
from flask.ext import wtf
from flask.ext.admin import expose
from flask.ext.admin.model import InlineFormAdmin

from labmanager.scorm import get_authentication_scorm
from labmanager.models import Credential, LMS, Course
from labmanager.views.admin import L4lModelView

config = yload(open('labmanager/config.yaml'))

class CredentialForm(InlineFormAdmin):
    form_columns = ('id','kind', 'key', 'secret')
    excluded_form_fields = ('id',)

    def postprocess_form(self, form):
        sel_choices =  [ (x , x.title()) for x in config['authentication_types']]
        form.kind = wtf.SelectField(u'Kind', choices=sel_choices)
        return form

def download(c, lms, p):
    for auth in lms.authentications:
        if auth.kind == 'basic':
            return Markup('<a href="%s">Download</a>' % (url_for('.scorm_authentication', id = lms.id)))
    return 'N/A'

class LMSPanel(L4lModelView):

    inline_models = (CredentialForm(Credential),)

    column_list = ('name', 'url', 'download')
    column_formatters = dict( download = download )


    def __init__(self, session, **kwargs):
        super(LMSPanel, self).__init__(LMS, session, **kwargs)
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

    @expose('/<id>/scorm_authentication.zip')
    def scorm_authentication(self, id):
        lms = self.session.query(LMS).filter_by(id = id).one()
        return get_authentication_scorm(lms.url)
            

class CoursePanel(L4lModelView):
    def __init__(self, session, **kwargs):
        super(CoursePanel, self).__init__(Course, session, **kwargs)

