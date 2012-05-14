from flask import Flask, request, Response
from functools import wraps
app = Flask(__name__)

DEBUG = True


def check_auth(username, password):
    return username == 'admin' and password == 'secret'

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

@app.route("/users/<user>")
def users(user = None):
    return "Hi, %s" % user

if __name__ == "__main__":
    app.run(debug=DEBUG)
