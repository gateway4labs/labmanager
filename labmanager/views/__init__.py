# -*-*- encoding: utf-8 -*-*-
# 
# lms4labs is free software: you can redistribute it and/or modify
# it under the terms of the BSD 2-Clause License
# lms4labs is distributed in the hope that it will be useful,
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
from flask import request

# 
# LabManager imports
# 

from labmanager.application import app

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
            print "Invalid JSON found"
            print "Suggested JSON: %r" % data
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
        return "Error opening provided URL"

    try:
        return json.loads(json_results)
    except:
        print "Invalid JSON", json_results
        return "Invalid JSON"

###############################################################################
# 
# 
# 

@app.errorhandler(404)
def not_found(e):
    return "404 not found", 404

@app.errorhandler(403)
def forbidden(e):
    return "403 forbidden", 403

@app.errorhandler(412)
def precondition_failed(e):
    return "412 precondition failed", 412

def load():
    import labmanager.views.ims_lti
    assert labmanager.views.ims_lti != None

    import labmanager.views.lms
    assert labmanager.views.lms != None

    import labmanager.views.lms_admin
    assert labmanager.views.lms_admin != None

    import labmanager.views.admin
    assert labmanager.views.admin != None
