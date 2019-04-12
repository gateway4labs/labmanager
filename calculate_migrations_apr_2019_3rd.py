from __future__ import print_function

import os
import json
import datetime
import urlparse

import requests

from flask import url_for

from labmanager import app
from labmanager.db import db
from labmanager.models import EmbedApplication, EmbedApplicationTranslation, HttpsUnsupportedUrl, UseLog
from labmanager.rlms import find_smartgateway_html_link

app.config['SERVER_NAME'] = 'gateway.golabz.eu'
app.config['PREFERRED_URL_SCHEME'] = 'https'



with app.app_context():
#    if os.path.exists('golabz.json'):
#        golabz_labs = json.load(open('golabz.json'))
#    else:
    if True:
        golabz_labs = requests.get("https://www.golabz.eu/rest/labs/retrieve.json").json()
        open('golabz.json', 'w').write(json.dumps(golabz_labs, indent=4))

    golabz_changes = [
        # {
        #   "id": "99",
        #   "add": [
        #      {
        #          'app_url': '...',
        #          'app_title': '...',
        #          'app_format': 'html'
        #      }
        #   ],
        #   'delete': [
        #      { 
        #         'app_url': '...'
        #      }
        #   ]
        # }
    ]

    for golab_lab in golabz_labs:
        for golab_lab_app in golab_lab['lab_apps']:
            golabz_url = golab_lab_app['app_url']

            url_parsed = urlparse.urlparse(golabz_url)
            if url_parsed.netloc != 'gateway.golabz.eu':
                continue

            if url_parsed.path.endswith('.xml'):

                # If it is in Graasp, replace it
                golab_lab_id = golab_lab['id']

                existing_record = None
                for record in golabz_changes:
                    if record['id'] == golab_lab_id:
                        existing_record = record
                        break

                if existing_record is None:
                    existing_record = {
                        'id': golab_lab_id,
                        'add': [],
                        'delete': [],
                    }
                    golabz_changes.append(existing_record)

                replaced_url = golabz_url
                new_url = golabz_url
                if new_url.startswith('http://'):
                    new_url = new_url.replace('http://', 'https://', 1)

                new_url = new_url[::-1].replace('.xml'[::-1], '.html'[::-1], 1)[::-1]

                existing_record['add'].append({
                    'app_url': new_url,
                    'app_title': golab_lab_app['app_title'],
                    'app_format': 'html',
                })
                existing_record['delete'].append({
                    'app_url': replaced_url,
                })

    open('migration_apr_2019/golabz_replacements_3rd.json', 'w').write(json.dumps(golabz_changes, indent=4))
