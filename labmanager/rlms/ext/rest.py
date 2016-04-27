# -*-*- encoding: utf-8 -*-*-
# 
# gateway4labs is free software: you can redistribute it and/or modify
# it under the terms of the BSD 2-Clause License
# gateway4labs is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

import sys
import json

import requests
import traceback

from flask import current_app
from flask.ext.wtf import TextField, Required, URL, PasswordField, SelectField

from labmanager.forms import AddForm, RetrospectiveForm, GenericPermissionForm
from labmanager.rlms import register, Laboratory, BaseRLMS, BaseFormCreator, Versions, Capabilities

def get_module(version):
    return sys.modules[__name__]

class HttpAddForm(AddForm):

    base_url = TextField("Base URL",    validators = [Required(), URL(False) ])
    login    = TextField("Login",    validators = [Required() ])
    password = PasswordField("Password",    validators = [])
    extension = TextField("Extension",    validators = [], description = "If required, provide an extension (e.g., .php) to the HTTP API")
    mode = SelectField("Mode",  choices=[('json', 'Pure JSON requests and responses'), ('json+form', 'JSON for responses, HTML forms for requests')], default = "json")

    def __init__(self, add_or_edit, *args, **kwargs):
        super(HttpAddForm, self).__init__(*args, **kwargs)

    @staticmethod
    def process_configuration(old_configuration, new_configuration):
        return new_configuration

class HttpPermissionForm(RetrospectiveForm):
    pass

class HttpLmsPermissionForm(HttpPermissionForm, GenericPermissionForm):
    pass

class HttpFormCreator(BaseFormCreator):

    def get_add_form(self):
        return HttpAddForm

    def get_permission_form(self):
        return HttpPermissionForm

    def get_lms_permission_form(self):
        return HttpLmsPermissionForm

FORM_CREATOR = HttpFormCreator()

class RLMS(BaseRLMS):

    def __init__(self, configuration):
        self.configuration = configuration

        config = json.loads(configuration or '{}')
        self.base_url = config.get('base_url')
        if self.base_url.endswith('/'):
            self.base_url = self.base_url[:-1]

        self.login    = config.get('login')
        self.password = config.get('password')
        self.extension = config.get('extension', '')
        self.context_id = str(config.get('context_id', ''))
        self.mode = config.get('mode', 'json')

        if not self.base_url or not self.login or not self.password:
            raise Exception("Laboratory misconfigured: fields missing" )

    def _inject_extension(self, remaining):
        method_and_get_query = remaining.split('?',1)
        if len(method_and_get_query) == 1:
            return method_and_get_query[0] + self.extension
        else: # 2
            method, get_query = method_and_get_query
            return method + self.extension + '?' + get_query

    def _request(self, remaining, headers = {}):
        remaining = self._inject_extension(remaining)

        if '?' in remaining:
            context_remaining = remaining + '&context_id=' + self.context_id
        else:
            context_remaining = remaining + '?context_id=' + self.context_id
        url = '%s%s' % (self.base_url, context_remaining)
        r = HTTP_PLUGIN.cached_session.get(url, auth = (self.login, self.password), headers = headers)
        r.raise_for_status()
        try:
            return r.json()
        except ValueError:
            raise

    def _request_post(self, remaining, data, headers = None):
        remaining = self._inject_extension(remaining)

        if headers is None:
            headers = {}
        if '?' in remaining:
            context_remaining = remaining + '&context_id=' + self.context_id
        else:
            context_remaining = remaining + '?context_id=' + self.context_id

        headers['Content-Type'] = 'application/json'
        if self.mode == 'json':
            data = json.dumps(data)
        elif self.mode == 'json+form':
            data = data
        else:
            raise Exception("Misconfigured mode: %s" % self.mode)

        # Cached session will not cache anything in a post. But if the connection already exists to the server, we still use it, becoming faster
        r = HTTP_PLUGIN.cached_session.post('%s%s' % (self.base_url, context_remaining), data = data, auth = (self.login, self.password), headers = headers)
        return r.json()

    def get_version(self):
        return Versions.VERSION_1

    def get_capabilities(self):
        capabilities = HTTP_PLUGIN.rlms_cache.get('capabilities')
        if capabilities is not None:
            return capabilities
            
        capabilities = self._request('/capabilities')
        HTTP_PLUGIN.rlms_cache['capabilities'] = capabilities['capabilities']
        return capabilities['capabilities']

    def setup(self, back_url):
        setup_url = self._request('/setup?back_url=%s' % back_url)
        return setup_url['url']

    def test(self):
        response = self._request('/test_plugin')
        valid = response.get('valid', False)
        if not valid:
            return response.get('error_messages', ['Invalid error message'])

    def get_laboratories(self, **kwargs):
        labs = HTTP_PLUGIN.rlms_cache.get('labs')
        if labs is not None:
            return labs

        labs = self._request('/labs')['labs']
        laboratories = []
        for lab in labs:
            laboratory = Laboratory(name = lab['name'], laboratory_id = lab['laboratory_id'], description = lab.get('description'), autoload = lab.get('autoload'))
            laboratories.append(laboratory)

        HTTP_PLUGIN.rlms_cache['labs'] = laboratories
        return laboratories

    def get_translations(self, laboratory_id, **kwargs):
        cache_key = 'translations-%s' % laboratory_id
        translations = HTTP_PLUGIN.rlms_cache.get(cache_key)
        if translations is not None:
            return translations

        try:
            translations_json = self._request('/translations?laboratory_id=%s' % requests.utils.quote(laboratory_id, ''))
        except:
            traceback.print_exc()
            raise

        HTTP_PLUGIN.rlms_cache[cache_key] = translations_json
        return translations_json

    def reserve(self, laboratory_id, username, institution, general_configuration_str, particular_configurations, request_payload, user_properties, *args, **kwargs):
        request = {
            'laboratory_id' :  laboratory_id,
            'username'    : username,
            'institution' : institution,
            'general_configuration_str' : general_configuration_str,
            'particular_configurations' : particular_configurations,
            'request_payload' : request_payload,
            'user_properties' : user_properties,
        }
        request.update(kwargs)
        debug_mode = kwargs.get('debug', False) and current_app.debug
        if debug_mode:
            open('last_request.txt','w').write(json.dumps(request, indent = 4))
        try:
            response = self._request_post('/reserve', request)
        except:
            if debug_mode:
                exc_info = traceback.format_exc()
                open('last_request.txt','a').write(exc_info)
            raise
        else:
            if debug_mode:
                open('last_request.txt','a').write(json.dumps(response, indent = 4))
        return {
            'reservation_id' : response['reservation_id'],
            'load_url' : response['load_url']
        }

    def load_widget(self, reservation_id, widget_name, **kwargs):
        response = self._request('/widget?widget_name=%s' % widget_name, headers = { 'X-G4L-reservation-id' : reservation_id })
        return {
            'url' : response['url']
        }

    def list_widgets(self, laboratory_id, **kwargs):
        widgets_json = self._request('/widgets?laboratory_id=%s' % requests.utils.quote(laboratory_id))
        widgets = []
        for widget_json in widgets_json['widgets']:
            widget = {
                'name' : widget_json['name'],
                'description' : widget_json.get('description',''),
            }
            widgets.append(widget)

        return widgets

PLUGIN_NAME = "HTTP plug-in"
PLUGIN_VERSIONS = ['1.0']

def populate_cache(rlms):
    capabilities = rlms.get_capabilities()
    for lab in rlms.get_laboratories():
        if Capabilities.TRANSLATIONS in capabilities:
            rlms.get_translations(lab.laboratory_id)
        if Capabilities.TRANSLATION_LIST in capabilities:
            rlms.get_translation_list(lab.laboratory_id)
    

HTTP_PLUGIN = register(PLUGIN_NAME, PLUGIN_VERSIONS, __name__)
HTTP_PLUGIN.add_local_periodic_task('Populating cache', populate_cache, minutes = 55)

