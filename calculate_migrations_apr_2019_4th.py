from __future__ import print_function

import os
import json
import datetime
import urlparse

import requests

from flask import url_for
from sqlalchemy import func

from labmanager import app
from labmanager.db import db
from labmanager.models import EmbedApplication, EmbedApplicationTranslation, HttpsUnsupportedUrl, UseLog
from labmanager.rlms import find_smartgateway_html_link

app.config['SERVER_NAME'] = 'gateway.golabz.eu'
app.config['PREFERRED_URL_SCHEME'] = 'https'



with app.app_context():
    graasp_changes = {}

    for url, in db.session.query(func.distinct(UseLog.url)).all():
        if len(url) < 255: # Dont use cutted ones
            url_parsed = urlparse.urlparse(url)
            if url_parsed.netloc == 'gateway.golabz.eu':
                replacement = url
                if url_parsed.path.endswith('.xml'):
                    replacement = replacement[::-1].replace('.xml'[::-1], '.html'[::-1], 1)[::-1]
                if replacement.startswith('http://'):
                    replacement = replacement.replace('http://', 'https://', 1)

                if replacement != url:
                    graasp_changes[url] = replacement

    open('migration_apr_2019/graasp_changes_2nd.json', 'w').write(json.dumps(graasp_changes, indent=4))
