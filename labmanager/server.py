#!/usr/bin/env python
#-*-*- encoding: utf-8 -*-*-

# 
# Python imports
import hashlib
import json
import cgi
import traceback
from functools import wraps

# 
# Flask imports
# 
from flask import Flask, Response, render_template, request, g

# 
# LabManager imports
# 
from labmanager.database import db_session
from labmanager.models import LMS

app = Flask(__name__)

@app.teardown_request
def shutdown_session(exception = None):
    db_session.remove()

###############################################################################
# 
# 
#
# I N T E R A C T I O N     W I T H     L M S 
#
# 
# 

# 
# LMS authentication
# 
def check_lms_auth(lmsname, password):
    hash_password = hashlib.new("sha", password).hexdigest()
    lms = db_session.query(LMS).filter_by(login = lmsname, password = hash_password).first()
    g.lms = lmsname
    return lms is not None

def requires_lms_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_lms_auth(auth.username, auth.password):
            return Response(
                    'Could not verify your access level for that URL.\n'
                    'You have to login with proper credentials', 401,
                    {'WWW-Authenticate': 'Basic realm="Login Required"'})
        return f(*args, **kwargs)
    return decorated


@app.route("/lms4labs/requests/", methods = ('GET', 'POST'))
@requires_lms_auth
def requests():
    """SCORM packages will perform requests to this method, which will 
    interact with the permitted laboratories"""

    courses         = request.json['courses']
    request_payload = request.json['request']
    general_role    = request.json['general-role']
    author          = request.json['author']

    return "Hi lms %s" % g.lms



###############################################################################
# 
# 
# 
# I N T E R A C T I O N     W I T H     L A B M A N A G E R   A D M I N  
# 
# 
# 

@app.route("/lms4labs/admin/")
def admin_index():
    return render_template("labmanager_admin/index.html")


@app.route("/")
def index():
    return render_template("index.html")


if __name__ == "__main__":
    DEBUG = True
    app.run(debug=DEBUG)
