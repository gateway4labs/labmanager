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
from labmanager.models import EmbedApplication, EmbedApplicationTranslation, HttpsUnsupportedUrl, UseLog

if not os.path.exists('migration_apr_2019/embed_changes.json'):
    print("migration_apr_2019/embed_changes.json not found")
    sys.exit(-1)

embed_changes = json.load(open('migration_apr_2019/embed_changes.json'))

with app.app_context():
    for embed_change in embed_changes:
        embed_app = db.session.query(EmbedApplication).filter_by(id=embed_change['id']).one()
        if embed_app.url != embed_change['old_url']:
            print("WARNING: id {}; expected {} but found {}. Skipping".format(embed_change['id'], embed_change['old_url'], embed_app.url))
            continue

        new_url = embed_change['new_url']
        proxy = embed_change['proxy']
        print("Changing {} for {} and proxy {}".format(embed_app.url, new_url, proxy))
        
        embed_app.uses_proxy = proxy
        embed_app.url = new_url
    db.session.commit()
