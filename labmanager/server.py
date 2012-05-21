import hashlib

from flask import Flask, request, Response
from functools import wraps

from labmanager.database import db_session
from labmanager.models import LMS

app = Flask(__name__)

DEBUG = True

@app.teardown_request
def shutdown_session(exception = None):
    db_session.remove()

def check_auth(username, password):
    hash_password = hashlib.new("sha", password).hexdigest()
    lms = db_session.query(LMS).filter_by(name = username, password = hash_password).first()
    return lms is not None

def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
    'Could not verify your access level for that URL.\n'
    'You have to login with proper credentials', 401,
    {'WWW-Authenticate': 'Basic realm="Login Required"'})

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

@app.route("/")
@requires_auth
def hello():
    return "Hi there!"


if __name__ == "__main__":
    app.run(debug=DEBUG)
