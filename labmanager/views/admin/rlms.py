# -*-*- encoding: utf-8 -*-*-
from yaml import load as yload

from flask.ext import wtf
from flask.ext.login import current_user
from flask.ext.admin.contrib.sqlamodel import ModelView

config = yload(open('labmanager/config.yaml'))

class RLMSPanel(ModelView):
    name = 'RLMS'
    category = 'ReLMS'
    form_columns = ('kind', 'location', 'url')
    column_exclude_list = ('version')
    sel_choices = []
    for ins_rlms in config['installed_rlms']:
        for ver in config['installed_rlms'][ins_rlms]:
            sel_choices.append(("%s<>%s" % (ins_rlms, ver),"%s - %s" % (ins_rlms.title(), ver)) )
    form_overrides = dict(kind=wtf.SelectField)
    form_args = dict(
        kind=dict( choices=sel_choices )
        )

    def on_model_change(self, form, model):
        rlms_ver = model.kind.split('<>')
        model.kind, model.version = rlms_ver[0], rlms_ver[1]
        pass

    def is_accesible(self):
        return current_user.is_authenticated()

class ExperimentPanel(ModelView):
    name = 'Experiments'
    category = 'ReLMs'
    pass

class PermissionPanel(ModelView):
    name = 'Permissions'
    def is_accessible(self):
        return current_user.is_authenticated()

    form_columns = ('newlms','newcourse','experiment','configuration','access')
    sel_choices = [(status, status.title()) for status in config['permission_status']]
    form_overrides = dict(access=wtf.SelectField)
    form_args = dict(
        access=dict( choices=sel_choices )
        )
