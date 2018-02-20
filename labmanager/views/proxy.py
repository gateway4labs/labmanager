import re
import time
import urlparse

import requests
from flask import Blueprint, Response, abort, stream_with_context, request, url_for, jsonify, current_app

from labmanager.db import db
from labmanager.models import AllowedHost

proxy_blueprint = Blueprint('proxy', __name__)

WHITELIST_REQUEST_HEADERS = ["Accept-Language", "Cache-Control", "Cookie", "If-Modified-Since", "User-Agent", "If-None-Match", "If-Unmodified-Since"]
WHITELIST_RESPONSE_HEADERS = ["ETag", "Content-Type", "Server", "Last-Modified", "Date", "Location"]

unfinished_regexps = [
    re.compile(""".* href='[^']*$"""),
    re.compile(""".* href="[^"]*$"""),
    re.compile(""".* src="[^"]*$"""),
    re.compile(""".* src='[^']*$"""),
]

def extract_base_url(url):
    parsed = urlparse.urlparse(url)
    new_path = parsed.path
    # Go to the last directory
    if '/' in new_path:
        new_path = new_path[:new_path.rfind('/')+1]
    messages_file_parsed = urlparse.ParseResult(scheme = parsed.scheme, netloc = parsed.netloc, path = new_path, params = '', query = '', fragment = '')
    return messages_file_parsed.geturl()

def make_url_absolute(relative_path, url):
    if relative_path.startswith(('http://', 'https://')):
        return relative_path
    return extract_base_url(url) + relative_path

SRC_RELATIVE_REGEXP = re.compile(r"""(<\s*(?!ng-[^<]*)[^<]*\s(src|href)\s*=\s*"?'?)(?!http://|https://|//|/|#|"|"#|'|'#| i)""")
SRC_ABSOLUTE_REGEXP = re.compile(r"""(<\s*(?!ng-[^<]*)[^<]*\s(src|href)\s*=\s*"?'?)(?!http://|https://|//|#|"|"#|'|'#| i)""")
URL_ABSOLUTE_REGEXP = re.compile(r"""([: ]url\()/""")

def inject_absolute_urls(output, url):
    base_url = extract_base_url(url)
    absolute_url = 'http://{}/'.format(urlparse.urlparse(url).netloc)

    scheme = 'https' if request.url.startswith('https://') else 'http://'

    absolute_proxied_url = url_for('.proxy', url=absolute_url, _external=True, _scheme=scheme)
    relative_proxied_url = url_for('.proxy', url=base_url, _external=True, _scheme=scheme)

    output = SRC_RELATIVE_REGEXP.sub(r"\1%s" % relative_proxied_url, output)
    output = SRC_ABSOLUTE_REGEXP.sub(r"\1%s" % absolute_proxied_url, output)
    output = URL_ABSOLUTE_REGEXP.sub(r"\1%s" % absolute_proxied_url, output)
    return output

def replace_links(block, url):
    block = inject_absolute_urls(block, url)
    return block

def generate(req, url):
    pending_data = ""

    for chunk in req.iter_content(chunk_size=1024):
        current_block = pending_data + chunk

        unfinished = False
        for unfinished_regexp in unfinished_regexps:
            if unfinished_regexp.match(current_block):
                unfinished = True

        if unfinished:
            pending_data = current_block
            continue

        # It is finished. Replace all
        current_block = replace_links(current_block, url)

        yield current_block
        pending_data = ""


ALLOWED_HOSTS = None
ALLOWED_HOSTS_LAST_UPDATE = 0 # Epoch

def get_allowed_hosts():
    global ALLOWED_HOSTS
    global ALLOWED_HOSTS_LAST_UPDATE

    EXPIRATION = 60 # 1 minute

    if time.time() - ALLOWED_HOSTS_LAST_UPDATE < EXPIRATION: # Less than a minute? Check
        return ALLOWED_HOSTS

    # Check list of allowed hosts
    allowed_hosts = [ ah.url for ah in db.session.query(AllowedHost).all() ]
    allowed_hosts = [ allowed_host for allowed_host in allowed_hosts if 'localhost' not in allowed_host and '127.0.' not in allowed_host and '192.168' not in allowed_host and '::1' not in allowed_host ]
    ALLOWED_HOSTS = allowed_hosts
    return ALLOWED_HOSTS


@proxy_blueprint.route('/<path:url>')
def proxy(url):
    if not url.startswith('http://'):
        return "Invalid protocol. Only http is supported -no https-.", 400

    parsed = urlparse.urlparse(url)
    if parsed.path == '':
        url = url + '/'

    if parsed.netloc not in get_allowed_hosts():
        return "URL domain not in the white list", abort(403)

    request_headers = {}
    for header in request.headers.keys():
        if header in WHITELIST_REQUEST_HEADERS:
            request_headers[header] = request.headers[header]

    req = requests.get(url, stream = True, headers=request_headers)

    content_type = req.headers.get('content-type')
    if content_type:
        kwargs = dict(content_type=content_type)
    else:
        kwargs = {}
    response = Response(stream_with_context(generate(req, url)), status=req.status_code, **kwargs)
    # req = requests.get(url, stream = True)
    # data = req.content
    # print len(data)
    # response = Response(data, content_type = req.headers['content-type'])
    for header in WHITELIST_RESPONSE_HEADERS:
        if header in req.headers.keys():
            header_value = req.headers[header]
            if header.lower() == 'location':
                if header_value.startswith('/'):
                    scheme = 'https' if request.url.startswith('https://') else 'http://'
                    header_value = url_for('.proxy', url='http://{}'.format(parsed.netloc), _external=True, _scheme=scheme) + header_value
            response.headers[header] = header_value
    return response

@proxy_blueprint.route('/allowed-hosts/', methods=['GET', 'POST'])
def allowed_hosts():
    if request.method == 'POST':
        data = request.get_json(force=True, silent=True)
        if request.headers.get('gw4labs-auth') != current_app.config.get('ALLOWED_HOSTS_CREDENTIAL', object()):
            return "Invalid gw4labs-auth credentials", 403

        # Valid app
        valid_hosts = data['hosts']

        processed_hosts = []
        for ah in db.session.query(AllowedHost).all():
            if ah.url in valid_hosts:
                ah.update()
            else:
                db.session.delete(ah)
            processed_hosts.append(ah.url)

        for missing_host in set(valid_hosts).difference(set(processed_hosts)):
            ah = AllowedHost(missing_host)
            db.session.add(ah)
        db.session.commit()

    all_hosts = [ {
        'url': ah.url,
        'when': ah.last_update.strftime("%Y-%m-%d %H:%M:%S")
    } for ah in db.session.query(AllowedHost).all() ]
    return jsonify(hosts=all_hosts)
