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
    if os.path.exists('golabz.json'):
        golabz_labs = json.load(open('golabz.json'))
    else:
        golabz_labs = requests.get("https://www.golabz.eu/rest/labs/retrieve.json").json()
        open('golabz.json', 'w').write(json.dumps(golabz_labs, indent=4))

    golabz_embedded_apps = {
        # identifier: { 
        #     'golabId': golab-id,
        #     'url': url
        # }
    }

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

    graasp_changes = {
        # 'old-url': 'new-url'
    }


    for golab_lab in golabz_labs:
        for golab_lab_app in golab_lab['lab_apps']:
            golabz_url = golab_lab_app['app_url']

            if 'gateway.golabz.eu/embed/apps/' in golabz_url:
                embed_identifier = golabz_url.split('/embed/apps/')[1].split('/app')[0]

                if embed_identifier in golabz_embedded_apps:
                    print("Repeated URL??? {}".format(embed_identifier))
                    continue

                golabz_embedded_apps[embed_identifier] = {
                    'golabId': golab_lab['id'],
                    'url': golabz_url,
                    'title': golab_lab_app['app_title'],
                }

            if golabz_url.startswith('http://gateway.golabz.eu/os/'):
                existing_record = None
                for record in golabz_changes:
                    if record['id'] == golab_lab['id']:
                        existing_record = record
                        break

                if existing_record is None:
                    existing_record = {
                        'id': golab_lab['id'],
                        'add': [],
                        'delete': [],
                    }
                    golabz_changes.append(existing_record)

                replacement = golabz_url.replace('http://', 'https://', 1) # Only once
                replacement = replacement[::-1] # Reverse
                replacement = replacement.replace('.xml'[::-1], '.html'[::-1], 1) # Only once
                replacement = replacement[::-1] # Reverse again

                existing_record['add'].append({
                    'app_url': replacement,
                    'app_title': golab_lab_app['app_title'],
                    'app_format': 'html',
                })
                existing_record['delete'].append({
                    'app_url': golabz_url,
                })
                graasp_changes[golabz_url] = replacement

    non_https_domains = [ url_db.url for url_db in db.session.query(HttpsUnsupportedUrl).all() ]

    embed_changes = [ 
        # {
        #   'id': EmbedApplication.id,
        #   'proxy': true/false
        #   'old_url': old_url
        #   'new_url': new_url
        # }
    ]

    # Let's check EmbedApplications
    for embed_app in db.session.query(EmbedApplication).all():

        url = embed_app.url

        smart_gateway_html_link = find_smartgateway_html_link(url)
        if smart_gateway_html_link is not None:
            if '/academo/' not in smart_gateway_html_link:
                # TODO: it is an opensocial link. It should be
                if embed_app.identifier in golabz_embedded_apps:
                    golab_lab_id = golabz_embedded_apps[embed_app.identifier]['golabId']

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

                    replaced_url = golabz_embedded_apps[embed_app.identifier]['url']

                    existing_record['add'].append({
                        'app_url': smart_gateway_html_link,
                        'app_title': golabz_embedded_apps[embed_app.identifier]['title'],
                        'app_format': 'html',
                    })
                    existing_record['delete'].append({
                        'app_url': replaced_url,
                    })


                    if replaced_url.startswith('https://'):
                        graasp_changes[replaced_url] = smart_gateway_html_link
                        graasp_changes[replaced_url.replace('https://', 'http://', 1)] = smart_gateway_html_link
                    else:
                        graasp_changes[replaced_url] = smart_gateway_html_link
                        graasp_changes[replaced_url.replace('http://', 'https://', 1)] = smart_gateway_html_link
            continue

        # This link is not in the Smart Gateway

        replaced_url_http = url_for('embed.app_xml', identifier=embed_app.identifier, _external=True).replace('https://', 'http://', 1)
        replaced_url_https = url_for('embed.app_xml', identifier=embed_app.identifier, _external=True).replace('http://', 'https://', 1)
        if replaced_url_http not in graasp_changes and replaced_url_https not in graasp_changes:
            graasp_changes[replaced_url_http] = url_for('embed.app_html', identifier=embed_app.identifier, _external=True).replace('http://', 'https://', 1)
            graasp_changes[replaced_url_https] = url_for('embed.app_html', identifier=embed_app.identifier, _external=True).replace('http://', 'https://', 1)

        if not url.startswith('http://'):
            # It's already in https
            continue

        if embed_app.uses_proxy:
            # Already supports https
            continue

        domain = urlparse.urlparse(url).netloc
        if domain == 'www.neuroproductions.be':
            # Just add the proxy
            embed_changes.append({
                'id': embed_app.id,
                'proxy': True,
                'old_url': url,
                'new_url': url,
            })
            continue

        if not any([ c.isalpha() for c in domain ]) or ':' in domain:
            # No alpha: it's just an IP address or it has a port; remain as http
            continue

        if embed_app.identifier in golabz_embedded_apps:

            # If it's in the golabz labs, then we can know that if the domain is not bad, it should not be bad
            if domain in non_https_domains:
                # Can't do anything about these
                continue

            # It is http, it's not in the Smart Gateway, but it does support https
            embed_changes.append({
                'id': embed_app.id,
                'proxy': False,
                'old_url': url,
                'new_url': url.replace('http://', 'https://', 1)
            })


        else:
            # It's not smartgateway-able, does not have https. Is it used?
            external_url_http = url_for('embed.app_xml', identifier=embed_app.identifier, _external=True).replace('http://', 'https://')
            external_url_https = url_for('embed.app_xml', identifier=embed_app.identifier, _external=True).replace('https://', 'http://')

            count = ( db.session.query(UseLog).filter_by(url=external_url_http).filter(UseLog.date > datetime.date(2019, 1, 1)).count() +
                      db.session.query(UseLog).filter_by(url=external_url_https).filter(UseLog.date > datetime.date(2019, 1, 1)).count() )

            # if count > 1:
            #     print (url, count)

    open('migration_apr_2019/embed_changes.json', 'w').write(json.dumps(embed_changes, indent=4))
    open('migration_apr_2019/golabz_replacements.json', 'w').write(json.dumps(golabz_changes, indent=4))
    open('migration_apr_2019/graasp_changes.json', 'w').write(json.dumps(graasp_changes, indent=4))
