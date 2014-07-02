import json
import requests
from flask import Flask, Response, request, Blueprint

app = Flask(__name__)

VERSION = 1

PLUGIN_USERNAME = 'labmanager'
PLUGIN_PASSWORD = 'password'

# So as to make the development easy, instead of a database we use a plugin_config.json file

CONFIG_FILE = 'plugin_config.json'

def get_config():
    return json.load(open(CONFIG_FILE))

def save_config(config):
    json.dump(config, open(CONFIG_FILE, 'w'))

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
# Static methods (e.g., 
# 

@plugin.route('/test-plugin')
def test_plugin():
    return json.dumps({
        'valid' : True,
        'g4l-api-version' : VERSION
    })

@plugin.route('/capabilities')
def capabilities():
    return json.dumps({
        'capabilities' : ['widget']
    })

@plugin.route('/setup')
def setup():
    pass # TODO

@plugin.route('/test-config')
def test_config():
    pass # TODO

@plugin.route('/labs')
def labs():
    pass # TODO

@plugin.route('/reserve', methods = ['GET', 'POST'])
def reserve():
    pass # TODO

# OPTIONAL: support for widgets
@plugin.route('/widgets')
def widgets():
    pass # TODO

@plugin.route('/widget')
def widget():
    pass # TODO

app.register_blueprint(plugin, url_prefix = '/plugin')

#################################
# 
# Setup application
# 
@app.route('/setup/')
def setup_app():
    return ":-)"

if __name__ == '__main__':
    app.run(port=5002, debug = True)
