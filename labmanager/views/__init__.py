# -*-*- encoding: utf-8 -*-*-
# 
# lms4labs is free software: you can redistribute it and/or modify
# it under the terms of the BSD 2-Clause License
# lms4labs is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

"""
  :copyright: 2012 Pablo Orduña, Elio San Cristobal, Alberto Pesquera Martín
  :license: BSD, see LICENSE for more details
"""

#
# Python imports
import json
import urlparse
import codecs
import os
import traceback
import StringIO
import zipfile
from functools import wraps
import urllib2

# 
# Flask imports
# 
from flask import Response, render_template, request, redirect, url_for, flash

# 
# LabManager imports
# 
from labmanager.database import db_session
from labmanager import app

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

def deletes_elements(table):
    def real_wrapper(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if request.method == 'POST' and request.form.get('action','') == 'delete':
                for current_id in request.form:
                    element = db_session.query(table).filter_by(id = current_id).first()
                    if element is not None:
                        db_session.delete(element)
                db_session.commit()

            return f(*args, **kwargs)
        return decorated
    return real_wrapper

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

    json_results= opener.open(req).read()
    try:
        return json.loads(json_results)
    except:
        print "Invalid JSON", json_results
        return None

###############################################################################
# 
# 
# 
#                S C O R M     M A N A G E M E N T
# 
# 
# 

def get_scorm_object(authenticate = True, laboratory_identifier = '', lms_path = '/', lms_extension = '/', html_body = '''<div id="lms4labs_root" />\n'''):
    import labmanager
    # TODO: better way
    base_dir = os.path.dirname(labmanager.__file__)
    base_scorm_dir = os.path.join(base_dir, 'data', 'scorm')
    if not os.path.exists(base_scorm_dir):
        flash("Error: %s does not exist" % base_scorm_dir)
        return render_template("lms_admin/scorm_errors.html")

    sio = StringIO.StringIO('')
    zf = zipfile.ZipFile(sio, 'w')
    for root, dir, files in os.walk(base_scorm_dir):
        for f in files:
            file_name = os.path.join(root, f)
            arc_name  = os.path.join(root[len(base_scorm_dir)+1:], f)
            content = codecs.open(file_name, 'rb', encoding='utf-8').read()
            if f == 'lab.html' and root == base_scorm_dir:
                content = content % { 
                            u'EXPERIMENT_COMMENT'    : '//' if authenticate else '',
                            u'AUTHENTICATE_COMMENT'  : '//' if not authenticate else '',
                            u'EXPERIMENT_IDENTIFIER' : unicode(laboratory_identifier),
                            u'LMS_URL'               : unicode(lms_path),
                            u'LMS_EXTENSION'         : unicode(lms_extension),
                            u'HTML_CONTENT'          : unicode(html_body),
                        }
            zf.writestr(arc_name, content.encode('utf-8'))

    zf.close()
    return sio.getvalue()

def get_authentication_scorm(lms_url):
    lms_path = urlparse.urlparse(lms_url).path or '/'
    extension = '/'
    if 'lms4labs/' in lms_path:
        extension = lms_path[lms_path.rfind('lms4labs/lms/list') + len('lms4labs/lms/list'):]
        lms_path  = lms_path[:lms_path.rfind('lms4labs/')]

    content = get_scorm_object(True, lms_path=lms_path, lms_extension=extension)
    return Response(content, headers = {'Content-Type' : 'application/zip', 'Content-Disposition' : 'attachment; filename=authenticate_scorm.zip'})

###############################################################################
# 
# 
# 
#                G E N E R A L     V I E W
# 
# 
# 

@app.route("/fake_list_courses/lms4labs/list", methods = ['GET','POST'])
def fake_list_courses():
    # return """{"start":"2","number":3,"per-page":2,"courses":[{"id":"4","name":"example3"}]}"""
    auth = request.authorization
    if auth is None or auth.username not in ('test','labmanager') or auth.password not in ('test','password'):
        return Response('You have to login with proper credentials', 401,
                        {'WWW-Authenticate': 'Basic realm="Login Required"'})

    q         = request.args.get('q','')
    start_str = request.args.get('start','0')

    try:
        start = int(start_str)
    except:
        return "Invalid start"

    fake_data = []
    for pos in xrange(10000):
        if pos % 3 == 0:
            fake_data.append((str(pos), "Fake electronics course %s" % pos))
        elif pos % 3 == 1:
            fake_data.append((str(pos), "Fake physics course %s" % pos))
        else:
            fake_data.append((str(pos), "Fake robotics course %s" % pos))

    fake_return_data = []
    for key, value in fake_data:
        if q in value:
            fake_return_data.append({
                'id'   : key,
                'name' : value,
            })

    N = 10

    view = {
        'start'    : start,
        'number'   : len(fake_return_data),
        'per-page' : N,
        'courses'  : fake_return_data[start:start+N],
    }

    return json.dumps(view, indent = 4)


@app.route("/fake_lms/lms4labs/lms/forward", methods = ['GET','POST'])
def fake_lms_forward():
    json_data = get_json()
    if json_data is None:
        return "Could not parse JSON"
    
    assert json_data['action'], "reserve"

    experiment = json_data['experiment']

    msg = app.config.get('FAKE_LMS_MSG')
    if msg is not None:
        if '%' in msg:
            return msg % experiment
        return msg
    return ":-S"

@app.route("/fake_lms/lms4labs/lms/authenticate")
def fake_lms_authenticate():
    msg = app.config.get('FAKE_LMS_MSG')
    if msg is not None:
        return msg
    return ":-S"

@app.route("/lms4labs/labmanager/")
def lms4labs_labmanager_index():
    return render_template("index.html")

@app.route("/lms4labs/")
def index():
    return redirect(url_for('lms4labs_labmanager_index'))


@app.route("/")
def global_index():
    return redirect(url_for('lms4labs_labmanager_index'))

@app.route('/favicon.ico')
def favicon():
    return redirect(url_for('static', filename='favicon.ico'))

def load():
    import labmanager.views.lms
    assert labmanager.views.lms != None

    import labmanager.views.lms_admin
    assert labmanager.views.lms_admin != None

    import labmanager.views.labmanager_admin
    assert labmanager.views.labmanager_admin != None


