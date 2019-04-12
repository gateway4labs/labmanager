from __future__ import print_function

import os
import sys
import json
import datetime
import urlparse

import requests

from flask import url_for

from labmanager import app
from labmanager.db import db
from labmanager.models import UseLog

if not os.path.exists('migration_apr_2019/graasp_changes.json'):
    print("migration_apr_2019/graasp_changes.json not found")
    sys.exit(-1)

graasp_changes = json.load(open('migration_apr_2019/graasp_changes.json'))

with app.app_context():
    for old_url, new_url in graasp_changes.items():
        old_url = old_url[:255]
        new_url = new_url[:255]
        for log in db.session.query(UseLog).filter_by(url=old_url).all():
            log.url = new_url

    db.session.commit()
