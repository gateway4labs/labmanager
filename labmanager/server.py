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

DEBUG = True

@app.teardown_request
def shutdown_session(exception = None):
    db_session.remove()

def check_lms_auth(lmsname, password):
    hash_password = hashlib.new("sha", password).hexdigest()
    lms = db_session.query(LMS).filter_by(name = lmsname, password = hash_password).first()
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

def requires_json(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            g.json_data = json.loads(request.data)
        except:
            return Response('Could not parse required JSON request', 400)
        return f(*args, **kwargs)
    return decorated


@app.route("/lms4labs/requests/", methods = ('GET', 'POST'))
@requires_lms_auth
@requires_json
def requests():
    courses = g.json_data['courses']
    return "Hi lms %s" % g.lms

@app.route("/")
def hello():
    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=DEBUG)
