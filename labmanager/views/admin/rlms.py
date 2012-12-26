# -*-*- encoding: utf-8 -*-*-
import json
from yaml import load as yload

from flask import request, abort
from flask.ext import wtf
from flask.ext.login import current_user
from flask.ext.admin.contrib.sqlamodel import ModelView

from labmanager.models import Permission, Experiment, NewRLMS
from labmanager.rlms import get_form_class

config = yload(open('labmanager/config.yaml'))

class DynamicSelectWidget(wtf.widgets.Select):
    def __call__(self, *args, **kwargs):
        html = super(DynamicSelectWidget, self).__call__(*args, **kwargs)
        html = html.replace('<select ', '''<select onchange="document.location.replace(new String(document.location).replace(/&rlms=[^&]*/,'') + '&rlms=' + this.value)"''')
        return html

class DynamicSelectField(wtf.SelectField):
    widget = DynamicSelectWidget()

class RLMSPanel(ModelView):

    form_columns = ('kind', 'location', 'url')
    column_exclude_list = ('version')
    sel_choices = [('','')]
    for ins_rlms in config['installed_rlms']:
        for ver in config['installed_rlms'][ins_rlms]:
            sel_choices.append(("%s<>%s" % (ins_rlms, ver),"%s - %s" % (ins_rlms.title(), ver)) )
    form_overrides = dict(kind=DynamicSelectField)
    form_args = dict( kind=dict( choices=sel_choices ))

    def __init__(self, session, **kwargs):

        default_args = { "category":u"ReLMS", "name":u"RLMS" }
        default_args.update(**kwargs)

        super(RLMSPanel, self).__init__(NewRLMS, session, **default_args)
        
        # 
        # For each supported RLMS, it provides a different edition
        # form. So as to avoid creating a new class each type for 
        # the particular form required, we must create a cache of
        # form classes.
        #
        self.__create_form_classes = {}
   
    def _get_cached_form_class(self, rlms, form):
        if rlms in self.__create_form_classes:
            form_class = self.__create_form_classes[rlms]
        else:
            # If it does not exist, we find the RLMS creation form
            rlmstype, rlmsversion = rlms.split('<>')
            rlms_form_class = get_form_class(rlmstype, rlmsversion)
            
            # And we create and register a new class for it
            class form_class(rlms_form_class, form.__class__):
                pass
            self.__create_form_classes[rlms] = form_class
        return form_class

    def _fill_form_instance(self, form, old_form, obj):
        form.csrf_token.data = old_form.csrf_token.data
        form.process(obj=obj)
        form.csrf_token.data = old_form.csrf_token.data

        for key in form.get_field_names():
            if key in request.form:
                getattr(form, key).data = request.form[key]

    def create_form(self, obj = None, *args, **kwargs):
        form = super(RLMSPanel, self).create_form(*args, **kwargs)
        rlms = request.args.get('rlms')

        if rlms is not None and '<>' in rlms:
            form_class = self._get_cached_form_class(rlms, form)

            old_form = form
            form = form_class(add_or_edit=True, fields=form._fields)
            form.kind.default = rlms
            self._fill_form_instance(form, old_form, obj)
        return form

    def edit_form(self, obj, *args, **kwargs):
        form = super(RLMSPanel, self).edit_form(*args, **kwargs)
        form_class = self._get_cached_form_class(obj.kind + u'<>' + obj.version , form)
        old_form = form
        form = form_class(add_or_edit=False, fields=form._fields)
        del form.kind
        
        configuration = json.loads(obj.configuration)
        for key in configuration:
            # TODO: this should be RLMS specific
            if 'password' not in key: 
                setattr(obj, key, configuration[key])

        self._fill_form_instance(form, old_form, obj )
        return form

    def on_model_change(self, form, model):
        if model.kind == '':
            abort(406)
        
        if '<>' in model.kind:
            rlms_ver = model.kind.split('<>')
            model.kind, model.version = rlms_ver[0], rlms_ver[1]

        if not model.configuration:
            other_data = {}
        else:
            other_data = json.loads(model.configuration)

        for key in form.get_field_names():
            if key not in RLMSPanel.form_columns:
                # TODO: this should be RLMS specific
                if 'password' in key and getattr(form, key).data == '':
                    pass # Passwords can be skipped
                else:
                    other_data[key] = getattr(form, key).data
        
        model.configuration = json.dumps(other_data)

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
