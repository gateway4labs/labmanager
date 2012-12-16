from hashlib import new as new_hash

from functools import wraps

from flask import Response, render_template, request, g, abort, flash, redirect, url_for
from flask.ext.login import LoginManager, login_user, logout_user, login_required

from labmanager import app
from labmanager.views import get_json
from labmanager.database import db_session
from labmanager.models import LMS, LabManagerUser as User, Credential

from ims_lti_py import ToolProvider

login_manager = LoginManager()

def init_login(labmanager):
    login_manager.setup_app(labmanager)
    login_manager.session_protection = "strong"

@login_manager.user_loader
def load_user(userid):
    return User.find(int(userid))

@app.before_first_request
def verify_credentials():
    auth = None

    if 'oauth_consumer_key' in request.form:
        consumer_key = request.form['oauth_consumer_key']
        auth = Credential.find_by_key(consumer_key)

        # check for nonce
        # check for old requests
        # Cross reference information

        if auth is None:
            abort(412)

        secret = auth.secret
        tool_provider = ToolProvider(consumer_key, secret, request.form.to_dict())

        if (tool_provider.valid_request(request) == False):
            abort(403)

    elif request.authorization:
        requires_lms_auth()
        return

    else:
        flash('Bypassing authorization')
        return


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST' and 'username' in request.form:
        username = request.form['username']
        hashed = new_hash("sha", request.form['password']).hexdigest()
        user = User.exists(username, hashed)
        if user is not None:
            if login_user(user):
                return redirect(url_for('admin.index'))
            else:
                flash(u'Could not log in.')
        else:
            flash(u'Invalid username.')
    return render_template('login.html')

@app.route("/logout", methods=['GET'])
@login_required
def logout():
    logout_user()
    return redirect('login')

#
# LMS authentication
#
def check_lms_auth(lmsname, password):
    hash_password = new_hash("sha", password).hexdigest()
    lms = db_session.query(LMS).filter_by(lms_login = lmsname, lms_password = hash_password).first()
    g.lms = lmsname
    return lms is not None

def requires_lms_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        login_required = Response(
                    'Could not verify your access level for that URL.\n'
                    'You have to login with proper credentials', 401,
                    {'WWW-Authenticate': 'Basic realm="Login Required"'})

        auth = request.authorization
        if not auth:
            json_data = get_json()
            if json_data is None:
                return login_required
            username = json_data.get('lms_username','')
            password = json_data.get('lms_password','')
        else:
            username = auth.username
            password = auth.password

        if not check_lms_auth(username, password):
            return login_required

        return f(*args, **kwargs)
    return decorated
