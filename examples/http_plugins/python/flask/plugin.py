import os
import uuid
import json
import datetime
import requests
from flask import Flask, Response, request, Blueprint, url_for, render_template

app = Flask(__name__)

VERSION = 1

PLUGIN_USERNAME = 'labmanager'
PLUGIN_PASSWORD = 'password'

LAB_ID = 'sample lab'
LAB_URL = 'http://localhost:5001/lab'
LAB_LOGIN = 'myplugin'

# So as to make the development easy, instead of a database we use a plugin_config.json file

CONFIG_FILE = 'plugin_config.json'

def get_context_id():
    context_id = request.args.get('context_id')
    if not context_id:
        raise Exception("context_id is mandatory")
    return str(context_id)


def get_config():
    if os.path.exists(CONFIG_FILE):
        all_configuration = json.load(open(CONFIG_FILE))
        context_id = get_context_id()        
        return all_configuration.get(context_id, {})
    else:
        return {}

def save_config(config):
    if os.path.exists(CONFIG_FILE):
        all_configuration = json.load(open(CONFIG_FILE))
    else:
        all_configuration = {}
    context_id = get_context_id()
    all_configuration[context_id] = config
    json.dump(all_configuration, open(CONFIG_FILE, 'w'))

# 
# First, the credentials management. In Flask, this is applied to all the
# web methods of this Blueprint.
# 
plugin = Blueprint('plugin', __name__)
@plugin.before_request
def check_credentials():
    UNAUTHORIZED = Response(response="Could not verify your credentials", status=401, headers = {'WWW-Authenticate':'Basic realm="Login Required"'})
    auth = request.authorization
    if not auth:
        return UNAUTHORIZED
    if auth.username != PLUGIN_USERNAME or auth.password != PLUGIN_PASSWORD:
        return UNAUTHORIZED
    
    # It's valid
    return None

# 
# Static methods (e.g., plug-in capabilities or version) 
# 

@plugin.route('/test_plugin')
def test_plugin():
    return json.dumps({
        'valid' : True,
        'g4l-api-version' : VERSION
    }, indent = 4)

@plugin.route('/capabilities')
def capabilities():
    return json.dumps({
        'capabilities' : ['widget']
    }, indent = 4)

@plugin.route('/labs')
def labs():
    # This can be retrieved from a database, or by contacting the laboratory
    # in case it manages more than one laboratory.
    return json.dumps({
           'labs' : [
              {
                  'name' : 'Sample laboratory',
                  'description' : 'This is an example of laboratory',
                  'autoload' : False,
                  'laboratory_id' : LAB_ID,
              }
           ]
        }, indent = 4)

# OPTIONAL: support for widgets
@plugin.route('/widgets')
def widgets():
    lab_id = request.args.get('laboratory_id')
    if lab_id != LAB_ID:
        return "Lab not found", 404
    # This can be retrieved from a database, or by contacting the laboratory
    # in case it manages more than one laboratory.
    return json.dumps({
           'widgets' : [
                {
                   'name'        : 'camera1',
                   'description' : 'Left camera'
                },
                {
                   'name'        : 'camera2',
                   'description' : 'Right camera'
                },
           ]
        }, indent = 4)

@plugin.route('/widget')
def widget():
    reservation_id = request.headers.get('X-G4L-reservation-id')
    widget_name = request.args.get('widget_name')
    if widget_name == 'camera1':
        return json.dumps({
                'url' : '%s/camera1/?reservation_id=%s' % (LAB_URL, reservation_id)
            }, indent = 4)
    elif widget_name == 'camera2':
        return json.dumps({
                'url' : '%s/camera2/?reservation_id=%s' % (LAB_URL, reservation_id)
            }, indent = 4)
    return "widget not found", 404


# 
#
# Methods that actually connect to the final laboratory:
# - test_config()
# - reserve()
# 
# 


@plugin.route('/test_config')
def test_config():
    config = get_config()
    r = requests.get('%(base_url)s/test/?system_login=%(login)s&system_password=%(password)s' % {
        'base_url' : LAB_URL,
        'login'    : LAB_LOGIN,
        'password' : config.get('password', ''),
    })
    if r.text == 'ok':
        return json.dumps({
           'valid' : True
        }, indent = 4)
    return json.dumps({
        'valid' : False,
        'error-messages' : [r.text]
    }, indent = 4)

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
            print "Suggested JSON:", data
            traceback.print_exc()
            return None

@plugin.route('/reserve', methods = ['GET', 'POST'])
def reserve():
    config = get_config()
    if request.method == 'POST':
        request_json = get_json()
        # a dictionary including: laboratory_id, username, institution, general_configuration, particular_configuration, request_payload (if any), user_properties (full name, from ip, etc.), etc.
        if not request_json:
            return "Invalid JSON document", 400
        username = u'%s@%s' % (request_json.get('username'), request_json.get('institution'))
        back_url = request_json.get('back')
    else:
        username = 'username not provided'
        back_url = 'https://github.com/gateway4labs/'

    reservation_url = '%(url)s/reserve/?system_login=%(login)s&system_password=%(password)s&username=%(username)s&back_url=%(back_url)s' % {
                            'url' : LAB_URL,
                            'login' : LAB_LOGIN,
                            'password' : config.get('password', ''),
                            'username' : username,
                            'back_url' : back_url,
                        }
    r = requests.get(reservation_url)
    response = r.json()
    return json.dumps({
            'load_url' : response['url'],
            'reservation_id' : response['reservation_id']
        }, indent = 4)


#################################
# 
# Setup application
# 

@plugin.route('/setup')
def setup():
    back_url = request.args.get('back_url')
    reservation_id = str(uuid.uuid4())
    RESERVATIONS[reservation_id] = { 'expires' : datetime.datetime.now() + datetime.timedelta(seconds = 5 * 60) }
    if back_url:
        RESERVATIONS[reservation_id]['back_url'] = back_url
    return json.dumps({
        'url' : url_for('setup_app', reservation_id = reservation_id, context_id = request.args.get('context_id'), _external = True)
    }, indent = 4)


# memcached, redis, database or whatever. For the sake of simplicity memory is used
RESERVATIONS = {
    # 'reservation_identifier' : {
    #     'expires' : datetime.datetime.now() + 5 minutes
    #     'back_url' : 'url-to-go'
    # }
}


@app.route('/setup/', methods = ['GET', 'POST'])
def setup_app():
    reservation_id = request.args.get('reservation_id')
    if not reservation_id:
        return "Missing reservation_id"
    if reservation_id not in RESERVATIONS:
        return "reservation identifier not registered"
    context_id = request.args.get('context_id')
   
    reservation = RESERVATIONS[reservation_id]
    if request.method == 'POST':
        # CSRF not managed for the sake of simplicity
        password = request.form.get('password')
        save_config({ 'password' : password })

    current_password = get_config().get('password', '')
    current_password_correct = ( current_password == PLUGIN_PASSWORD ) 
    return render_template('plugin_form.html', reservation_id = reservation_id, current_password = current_password, current_password_correct = current_password_correct, back_url = reservation['back_url'], context_id = context_id)


app.register_blueprint(plugin, url_prefix = '/plugin')

if __name__ == '__main__':
    app.run(port=5002, debug = True)
