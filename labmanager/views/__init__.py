# -*-*- encoding: utf-8 -*-*-
# 
# gateway4labs is free software: you can redistribute it and/or modify
# it under the terms of the BSD 2-Clause License
# gateway4labs is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

#
# Python imports
import json
import traceback
import urllib2

# 
# Flask imports
# 
from flask import request, redirect, url_for
from flask.ext.admin import BaseView, expose
from labmanager.babel import gettext, ngettext, lazy_gettext

###################
# 
# Utility class
# 

class RedirectView(BaseView):

    def __init__(self, redirection_url, *args, **kwargs):
        self.redirection_url = redirection_url
        super(RedirectView, self).__init__(*args, **kwargs)

    @expose()
    def index(self):
        return redirect(url_for(self.redirection_url))

def get_json():
    if request.json is not None:
        return request.json
    else:
        try:
            if request.data:
                data = request.data
            else:
                keys = request.form.keys() or ['']
                data = keys[0]
            return json.loads(data)
        except:
            print gettext("Invalid JSON found")
            print gettext(u"Suggested JSON: %(rdata)r", rdata=data)
            traceback.print_exc()
            return None

###############################################################################
# 
# 
# 
#                L M S    I N T E R A C T I O N 
# 
# 
#

def retrieve_courses(url, user, password):
    req = urllib2.Request(url, '')
    req.add_header('Content-type','application/json')

    password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
    password_mgr.add_password(None, url, user, password)
    password_handler = urllib2.HTTPBasicAuthHandler(password_mgr)
    opener = urllib2.build_opener(password_handler)

    try:
        json_results= opener.open(req).read()
    except:
        traceback.print_exc()
        return gettext("Error opening provided URL")

    try:
        return json.loads(json_results)
    except:
        print gettext("Invalid JSON"), json_results
        return gettext("Invalid JSON")

###############################################################################
# 
# 
# 

def load():
    import labmanager.views.ims_lti
    assert labmanager.views.ims_lti != None

    import labmanager.views.lms
    assert labmanager.views.lms != None

    import labmanager.views.admin
    assert labmanager.views.admin != None
