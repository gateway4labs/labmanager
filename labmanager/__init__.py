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
# Flask imports
#
import os
from flask import Flask

app = Flask(__name__)
app.config.from_object('config')

from labmanager.database import db_session
from labmanager.views.admin import init_admin
from labmanager.views.login import init_login
init_admin(app, db_session)
init_login(app)

@app.teardown_request
def shutdown_session(exception = None):
    db_session.remove()

from labmanager.views import load
load()

def run():
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

if __name__ == "__main__":
    run()
