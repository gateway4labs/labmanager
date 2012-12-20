# -*-*- encoding: utf-8 -*-*-
from yaml import load as yload

from flask.ext import wtf
from flask.ext.login import current_user
from flask.ext.admin.contrib.sqlamodel import ModelView

from labmanager.models import Permission, Experiment, NewRLMS

config = yload(open('labmanager/config.yaml'))

class RLMSPanel(ModelView):
    def __init__(self, session, **kwargs):
        # You can pass name and other parameters if you want to
        default_args = { "category":u"ReLMS", "name":u"RLMS" }
        default_args.update(**kwargs)
        super(RLMSPanel, self).__init__(NewRLMS, session, **default_args)

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

    def is_accessible(self):
        return current_user.is_authenticated()

class ExperimentPanel(ModelView):
    def __init__(self, session, **kwargs):
        # You can pass name and other parameters if you want to
        default_args = { "category":u"ReLMS", "name":u"Experiments" }
        default_args.update(**kwargs)
        super(ExperimentPanel, self).__init__(Experiment, session, **default_args)

    def is_accessible(self):
        return current_user.is_authenticated()


class PermissionPanel(ModelView):
    def __init__(self, session, **kwargs):
        # You can pass name and other parameters if you want to
        default_args = { "name":u"Permissions" }
        default_args.update(**kwargs)
        super(PermissionPanel, self).__init__(Permission, session, **default_args)

    def is_accessible(self):
        return current_user.is_authenticated()

    form_columns = ('newlms','newcourse','experiment','configuration','access')
    sel_choices = [(status, status.title()) for status in config['permission_status']]
    form_overrides = dict(access=wtf.SelectField)
    form_args = dict(
        access=dict( choices=sel_choices )
        )
