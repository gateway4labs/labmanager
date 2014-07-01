import json
import requests
from flask import Flask, Response, request

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
# web methods.
# 
@app.before_request
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

@app.route('/plugin/test-plugin')
def test_plugin():
    return json.dumps({
        'valid' : True,
        'g4l-api-version' : VERSION
    })

@app.route('/plugin/capabilities')
def capabilities():
    return json.dumps({
        'capabilities' : ['widget']
    })

@app.route('/plugin/setup')
def setup():
    pass # TODO

@app.route('/plugin/test-config')
def test_config():
    pass # TODO

@app.route('/plugin/labs')
def labs():
    pass # TODO

@app.route('/plugins/reserve', methods = ['GET', 'POST'])
def reserve():
    pass # TODO

# OPTIONAL: support for widgets
@app.route('/plugin/widgets')
def widgets():
    pass # TODO

@app.route('/plugins/widget')
def widget():
    pass # TODO

if __name__ == '__main__':
    app.run(port=5002, debug = True)
