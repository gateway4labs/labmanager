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
from flask import Flask

app = Flask(__name__)

app.config.from_object('config')
app.config['DEBUGGING_REQUESTS'] = True

from labmanager.database import db_session

@app.teardown_request
def shutdown_session(exception = None):
    db_session.remove()

from labmanager.views import load
load()

def run():
    app.run(threaded = True, host = '0.0.0.0')

if __name__ == "__main__":
    run()

