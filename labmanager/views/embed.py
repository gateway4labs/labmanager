import traceback
import datetime
import certifi
import requests
from bs4 import BeautifulSoup
from flask import Blueprint, render_template, make_response, redirect, url_for, request, session, jsonify
from labmanager.views.authn import requires_golab_login, current_golab_user

from labmanager.db import db
from labmanager.babel import gettext, lazy_gettext
from labmanager.models import EmbedApplication, EmbedApplicationTranslation, GoLabOAuthUser, UseLog
from labmanager.models import HttpsUnsupportedUrl
from labmanager.rlms import find_smartgateway_link, find_smartgateway_opensocial_link
from labmanager.translator.languages import obtain_languages
from labmanager.utils import remote_addr

from flask.ext.wtf import Form
from wtforms import TextField, HiddenField, SelectMultipleField
from wtforms.validators import required
from wtforms.fields.html5 import URLField
from wtforms.widgets import HiddenInput, TextInput, CheckboxInput, html_params, HTMLString
from wtforms.widgets.html5 import URLInput

embed_blueprint = Blueprint('embed', __name__)

@embed_blueprint.context_processor
def inject_variables():
    return dict(current_golab_user=current_golab_user())

class AngularJSInput(object):
    def __init__(self, **kwargs):
        self._internal_kwargs = kwargs
        super(AngularJSInput, self).__init__()

    # Support render_field(form.field, ng_value="foo")
    # http://stackoverflow.com/questions/20440056/custom-attributes-for-flask-wtforms
    def __call__(self, field, **kwargs):
        for key in list(kwargs):
            if key.startswith('ng_'):
                kwargs['ng-' + key[3:]] = kwargs.pop(key)

        for key in list(self._internal_kwargs):
            if key.startswith('ng_'):
                kwargs['ng-' + key[3:]] = self._internal_kwargs[key]

        return super(AngularJSInput, self).__call__(field, **kwargs)

class AngularJSTextInput(AngularJSInput, TextInput):
    pass

class AngularJSURLInput(AngularJSInput, URLInput):
    pass

class AngularJSHiddenInput(AngularJSInput, HiddenInput):
    pass


class DivWidget(object):
    def __init__(self, padding = '10px'):
        self.padding = padding

    def __call__(self, field, **kwargs):
        kwargs.setdefault('id', field.id)
        html = ['<div %s>' % (html_params(**kwargs))]
        for subfield in field:
            html.append('<label class="checkbox-inline">%s %s</label>' % (subfield(), subfield.label.text))
        html.append('</div>')
        return HTMLString(''.join(html))


class MultiCheckboxField(SelectMultipleField):
    widget = DivWidget()
    option_widget = CheckboxInput()


CERTIFICATES_CHECKED = False

def check_certificates():
    """Some comodo certificates are wrong."""
    global CERTIFICATES_CHECKED
    
    if CERTIFICATES_CHECKED:
        return

    ca_file = certifi.where()
    with open('utils/comodo_domain_server_ca.crt', 'rb') as infile:
        comodo_ca = infile.read()

    with open(ca_file, 'rb') as infile:
        ca_file_contents = infile.read()

    if comodo_ca not in ca_file_contents:
        try:
            requests.get("https://cosci.tw/run/", timeout=(10, 10)).close()
        except:
            with open(ca_file, 'ab') as outfile:
                outfile.write(comodo_ca)

    CERTIFICATES_CHECKED = True

#
# App Composer checker
#
@embed_blueprint.route('/https-limitations/', methods=['GET', 'POST'])
def allowed_hosts():
    if request.method == 'POST':
        data = request.get_json(force=True, silent=True)
        if request.headers.get('gw4labs-auth') != current_app.config.get('ALLOWED_HOSTS_CREDENTIAL', object()):
            return "Invalid gw4labs-auth credentials", 403

        # Unsupported https URLs
        unsupported_urls = data['hosts']

        processed_hosts = []
        for huu in db.session.query(HttpsUnsupportedUrl).all():
            if huu.url in processed_hosts:
                hul.update()
            else:
                db.session.delete(huu)
            processed_hosts.append(huu.url)

        for missing_host in set(unsupported_urls).difference(set(processed_hosts)):
            huu = HttpsUnsupportedUrl(missing_host)
            db.session.add(huu)
        db.session.commit()

    all_hosts = [ {
        'url': huu.url,
        'when': huu.last_update.strftime("%Y-%m-%d %H:%M:%S")
    } for huu in db.session.query(HttpsUnsupportedUrl).all() ]
    return jsonify(hosts=all_hosts)



# 
# Public URLs
#

@embed_blueprint.route('/apps/')
def apps():
    applications = db.session.query(EmbedApplication).order_by(EmbedApplication.last_update).all()
    return render_template("embed/apps.html", user = current_golab_user(), applications = applications, title = gettext("List of applications"))

@embed_blueprint.route('/apps/<identifier>/')
def app(identifier):
    application = db.session.query(EmbedApplication).filter_by(identifier = identifier).first()
    if application is None:
        return render_template("embed/error.html", message = gettext("Application '{identifier}' not found").format(identifier=identifier), user = current_golab_user()), 404

    return render_template("embed/app.html", user = current_golab_user(), app = application, title = gettext("Application {name}").format(name=application.name))

@embed_blueprint.route('/apps/<identifier>/app-legacy.html')
def app_legacy_html(identifier):
    application = db.session.query(EmbedApplication).filter_by(identifier = identifier).first()
    if application is None:
        return jsonify(error=True, message="App not found")

    apps_per_language = {
        'en': application.full_url,
    }
    for translation in application.translations:
        apps_per_language[translation.language] = translation.full_url

    return render_template("embed/app-embedded.html", apps=apps_per_language)

@embed_blueprint.route('/apps/<identifier>/app.html')
def app_html(identifier):
    application = db.session.query(EmbedApplication).filter_by(identifier = identifier).first()
    if application is None:
        return render_template("embed/error.xml", user = current_golab_user(), message = gettext("Application '{identifier}' not found").format(identifier=identifier)), 404

    apps_per_language = {}
    languages = ['en']
    for translation in application.translations:
        apps_per_language[translation.language] = {
            'url': translation.url,
            'full_url': translation.full_url,
        }
        languages.append(translation.language)

    author = application.owner.display_name

    return render_template("embed/app-embed.html", author = author, user = current_golab_user(), identifier=identifier, app = application, languages=languages, apps_per_language = apps_per_language, title = gettext("Application {name}").format(name=application.name))

@embed_blueprint.route('/apps/<identifier>/app.xml')
def app_xml(identifier):
    application = db.session.query(EmbedApplication).filter_by(identifier = identifier).first()
    if application is None:
        return render_template("embed/error.xml", user = current_golab_user(), message = gettext("Application '{identifier}' not found").format(identifier=identifier)), 404

    apps_per_language = {}
    languages = ['en']
    for translation in application.translations:
        apps_per_language[translation.language] = {
            'url': translation.url,
            'full_url': translation.full_url,
        }
        languages.append(translation.language)

    author = application.owner.display_name

    response = make_response(render_template("embed/app.xml", author = author, user = current_golab_user(), identifier=identifier, app = application, languages=languages, apps_per_language = apps_per_language, title = gettext("Application {name}").format(name=application.name)))
    response.content_type = 'application/xml'
    return response

# 
# Management URLs
# 

@embed_blueprint.route('/')
@requires_golab_login
def index():
    applications = db.session.query(EmbedApplication).filter_by(owner = current_golab_user()).order_by(EmbedApplication.last_update).all()
    return render_template("embed/index.html", applications = applications, user = current_golab_user())

class SimplifiedApplicationForm(Form):
    name = TextField(lazy_gettext("Name:"), validators=[required()], widget = AngularJSTextInput(ng_model='embed.name', ng_enter="submitForm()"), description=lazy_gettext("Name of the resource"))
    age_ranges_range = HiddenField(lazy_gettext("Age ranges:"), validators=[], description=lazy_gettext("Select the age ranges this tool is useful for"))

    # The following are NOT REQUIRED
    description = TextField(lazy_gettext("Description:"), validators=[], widget = AngularJSTextInput(ng_model='embed.description', ng_enter="submitForm()"), description=lazy_gettext("Describe the resource in a few words"))
    domains_text = TextField(lazy_gettext("Domains:"), validators=[], widget = AngularJSTextInput(ng_enter="submitForm()"), description=lazy_gettext("Say in which domains apply to the resource (separated by commas): e.g., physics, electronics..."))

    url = URLField(lazy_gettext("Web:"), widget = AngularJSURLInput(ng_model='embed.url', ng_enter="submitForm()"), description=lazy_gettext("Web address of the resource"))
    height = HiddenField(lazy_gettext("Height:"), widget = AngularJSHiddenInput(ng_model='embed.height'))
    scale = HiddenField(lazy_gettext("Scale:"), widget = AngularJSHiddenInput(ng_model='embed.scale'))


class ApplicationForm(SimplifiedApplicationForm):
    url = URLField(lazy_gettext("Web:"), validators=[required()], widget = AngularJSURLInput(ng_model='embed.url', ng_enter="submitForm()"), description=lazy_gettext("Web address of the resource"))
    height = HiddenField(lazy_gettext("Height:"), validators=[required()], widget = AngularJSHiddenInput(ng_model='embed.height'))
    scale = HiddenField(lazy_gettext("Scale:"), validators=[required()], widget = AngularJSHiddenInput(ng_model='embed.scale'))

def obtain_formatted_languages(existing_language_codes):
    languages = [ (lang.split('_')[0], name) for lang, name in obtain_languages().items() if lang != 'en_ALL' and name != 'DEFAULT']

    return [ { 'code' : language, 'name' : name } for language, name in languages if language not in existing_language_codes]

def list_of_languages():
    return { key.split('_')[0] : value for key, value in obtain_languages().items() }
        
def _get_scale_value(form):
    if form.scale.data:
        try:
            scale = int(100 * float(form.scale.data))
        except ValueError:
            pass
        else:
            form.scale.data = unicode(scale)
            return scale
    return None

def get_url_metadata(url, timeout = 3):
    name = ''
    description = ''
    code = None
    x_frame_options = ''
    error_retrieving = False
    content_type = ''
    try:
        req = requests.get(url, timeout=(timeout, timeout), stream=True)
    except:
        traceback.print_exc()
        error_retrieving = True
    else:
        try:
            code = req.status_code
            x_frame_options = req.headers.get('X-Frame-Options', '').lower()
            content_type = req.headers.get('content-type', '').lower()
            if req.status_code == 200 and 'html' in req.headers.get('content-type', '').lower():
                # First megabyte maximum
                content = req.iter_content(1024 * 1024).next()
                soup = BeautifulSoup(content, 'lxml')
                name = (soup.find("title").text or '').strip()
                meta_description = soup.find("meta", attrs={'name': 'description'})
                if meta_description is not None:
                    meta_description_text = meta_description.attrs.get('content')
                    if meta_description_text:
                        description = (meta_description_text or '').strip()
            req.close()
        except:
            traceback.print_exc()

    return { 'name' : name, 'description': description, 'code': code, 'x_frame_options' : x_frame_options, 'error_retrieving' : error_retrieving, 'content_type' : content_type }

@embed_blueprint.route('/stats', methods = ['POST'])
def stats():
    url = request.args.get('url')
    timezone_minutes = request.args.get('timezone_minutes')
    ip_address = remote_addr()
    log = UseLog(url = url, ip_address = ip_address, web_browser = request.headers.get('User-Agent'), user_agent = request.user_agent, lang_header=request.headers.get('Accept-Language'), timezone_minutes=timezone_minutes)
    db.session.add(log)
    db.session.commit()
    return "This is only for local statistics. No personal information is stored."


@embed_blueprint.route('/sync', methods = ['GET'])
def sync():
    return "Not used anymore"
    composer_contents = requests.get('http://composer.golabz.eu/export-embed.json').json()
    current_users = { user.email: user for user in db.session.query(GoLabOAuthUser).all() }
    users_modified = 0
    users_added = 0
    for user in composer_contents['users']:
        if user['email'] in current_users:
            if current_users[user['email']].display_name != user['display_name']:
                current_users[user['email']].display_name = user['display_name']
                users_modified += 1
        else:
            db.session.add(GoLabOAuthUser(email=user['email'], display_name=user['display_name']))
            users_added += 1

    db.session.commit()
    # Users sync'ed

    current_apps_by_public_id = { app.identifier: app for app in db.session.query(EmbedApplication).all() }
    public_identifiers_by_db_id = { app.id : app.identifier for app in current_apps_by_public_id.values() }

    current_translation_urls = {
        # public_identifier: {
        #     'es': obj
        # }
    }

    for translation_db in db.session.query(EmbedApplicationTranslation).all():
        public_identifier = public_identifiers_by_db_id[translation_db.embed_application_id]
        if public_identifier not in current_translation_urls:
            current_translation_urls[public_identifier] = {}

        current_translation_urls[public_identifier][translation_db.language] = translation_db

    current_users = { user.email: user for user in db.session.query(GoLabOAuthUser).all() }

    # Now we have everything in memory. Let's process it
    apps_added = 0
    apps_modified = 0
    FORMAT = '%Y-%m-%dT%H:%M:%S'
    for app in composer_contents['apps']:
        creation = datetime.datetime.strptime(app['creation'], FORMAT)
        last_update = datetime.datetime.strptime(app['last_update'], FORMAT)
        owner = current_users[app['owner_mail']]

        if app['identifier'] in current_apps_by_public_id:
            modified = False
            current_app = current_apps_by_public_id[app['identifier']]

            if current_app.url != app['url']:
                modified = True
                current_app.url = app['url']

            if current_app.name != app['name']:
                modified = True
                current_app.name = app['name']

            if current_app.height != app['height']:
                modified = True
                current_app.height = app['height']
            
            if current_app.scale != app['scale']:
                modified = True
                current_app.scale = app['scale']

            if current_app.last_update != last_update:
                modified = True
                current_app.last_update = last_update

            if current_app.creation != creation:
                modified = True
                current_app.creation = creation


            current_translations = current_translation_urls.get(app['identifier'], {})
            for translation in app['translations']:
                if translation['language'] not in current_translations:
                    new_translation = EmbedApplicationTranslation(embed_application = current_app, url = translation['url'], language = translation['language'])
                    db.session.add(new_translation)
                    modified = True
                else:
                    if current_translations[translation['language']].url != translation['url']:
                        modified = True
                        current_translations[translation['language']].url = translation['url']

            if modified:
                apps_modified += 1
            
        else:
            new_app = EmbedApplication(url = app['url'], name = app['name'], owner = owner, height = app['height'], identifier = app['identifier'], creation = creation, last_update = last_update, scale = app['scale'])
            db.session.add(new_app)
            apps_added += 1
            for translation in app['translations']:
                new_translation = EmbedApplicationTranslation(embed_application = new_app, url = translation['url'], language = translation['language'])
                db.session.add(new_translation)

    db.session.commit()
    
    return "<html><body><p>Sync completed. Users modified: %s; Users added: %s; Apps modified: %s; Apps added: %s</p></body></html>" % (users_modified, users_added, apps_modified, apps_added)

def find_replacement(app):
    sg_replacement = find_smartgateway_opensocial_link(app.url)
    if sg_replacement:
        return sg_replacement
    return 'http://gateway.golabz.eu/embed/apps/{}/app.xml'.format(app.identifier)

@embed_blueprint.route('/migrations/appcomp2gw/graasp.json', methods = ['GET'])
def appcomp2gw_graasp_migration():
    replacements = {}

    for app in db.session.query(EmbedApplication).all():
        original_url = 'http://composer.golabz.eu/embed/apps/{}/app.xml'.format(app.identifier)
        replacements[original_url] = find_replacement(app)

    return jsonify(replacements=replacements, total=len(replacements))

@embed_blueprint.route('/migrations/appcomp2gw/golabz.json', methods = ['GET'])
def appcomp2gw_golabz_migration():
    try:
        labs = requests.get("http://www.golabz.eu/rest/labs/retrieve.json").json()
    except:
        return "Couldn't connect to golabz"

    lab_urls = set()
    for lab in labs:
        for lab_app in lab['lab_apps']:
            lab_urls.add(lab_app['app_url'])

    replacements = {}

    for app in db.session.query(EmbedApplication).all():
        original_url = 'http://composer.golabz.eu/embed/apps/{}/app.xml'.format(app.identifier)
        
        if original_url in lab_urls:
            replacements[original_url] = find_replacement(app)

    return jsonify(replacements=replacements, total=len(replacements))

def obtain_golabz_manual_data():
    try:
        labs = requests.get("http://www.golabz.eu/rest/labs/retrieve.json").json()
    except:
        return "Couldn't connect to golabz"

    lab_urls = set()
    labs_by_lab_url = {}
    for lab in labs:
        for lab_app in lab['lab_apps']:
            lab_urls.add(lab_app['app_url'])
            labs_by_lab_url[lab_app['app_url']] = lab

    replacements = []

    for app in db.session.query(EmbedApplication).all():
        original_url = 'http://composer.golabz.eu/embed/apps/{}/app.xml'.format(app.identifier)
        original2_url = 'http://gateway.golabz.eu/embed/apps/{}/app.xml'.format(app.identifier)
        
        if original_url in lab_urls or original2_url in lab_urls:
            sg_replacement = find_smartgateway_opensocial_link(app.url)
            if sg_replacement:
                if original_url in lab_urls:
                    current_url = original_url
                else:
                    current_url = original2_url

                replacements.append({
                    'old_url': current_url,
                    'new_url': sg_replacement,
                    'golabz_page': labs_by_lab_url[current_url]['lab_golabz_page'],
                    'golabz_author': labs_by_lab_url[current_url]['author'],
                    'title': labs_by_lab_url[current_url]['title'],
                    'gateway_author_name': app.owner.display_name,
                    'gateway_author_email': app.owner.email,
                })
    return replacements

@embed_blueprint.route('/migrations/appcomp2gw/golabz-manual.json', methods = ['GET'])
def appcomp2gw_golabz_manual_migration_json():
    replacements = obtain_golabz_manual_data()
    return jsonify(replacements=replacements, total=len(replacements))

@embed_blueprint.route('/migrations/appcomp2gw/golabz-manual.html', methods = ['GET'])
def appcomp2gw_golabz_manual_migration_html():
    replacements = obtain_golabz_manual_data()
    return render_template('embed/migration_appcomp2gw_golabz_manual.html', replacements=replacements)




@embed_blueprint.route('/create', methods = ['GET', 'POST'])
@requires_golab_login
def create():
    check_certificates()

    original_url = request.args.get('url')
    if original_url:
        bookmarklet_from = original_url
    else:
        bookmarklet_from = None

    original_application = None
    if original_url:
        applications = db.session.query(EmbedApplication).filter_by(url=original_url).all()
        if applications:
            original_application = applications[0]
            for app in applications:
                if len(app.translations) > len(original_application.translations):
                    original_application = app
                if app.name and not original_application.name:
                    original_application = app
                    continue
                if app.description and not original_application.description:
                    original_application = app
                    continue

    if original_application is not None:
        form = ApplicationForm(obj=original_application)
    else:
        form = ApplicationForm()

    if not form.url.data and original_url:
        form.url.data = original_url
        if not form.name.data:
            result = get_url_metadata(original_url, timeout = 5)
            if result['name']:
                form.name.data = result['name']
            if result['description'] and not form.description.data:
                form.description.data = result['description']

    if form.url.data:
        form.url.data = form.url.data.strip()

    if form.validate_on_submit():
        form_scale = _get_scale_value(form)
        application = EmbedApplication(url = form.url.data, name = form.name.data, owner = current_golab_user(), height=form.height.data, scale=form_scale, description=form.description.data, age_ranges_range = form.age_ranges_range.data)
        application.domains_text = form.domains_text.data
        db.session.add(application)
        try:
            db.session.commit()
        except Exception as e:
            traceback.print_exc()
            return render_template("embed/error.html", message = gettext("There was an error creating an application"), user = current_golab_user()), 500
        else:
            kwargs = {}
            if bookmarklet_from:
                kwargs['url'] = bookmarklet_from
            return redirect(url_for('.edit', identifier=application.identifier, **kwargs))
            
    return render_template("embed/create.html", form=form, header_message=gettext("Add a web"), user = current_golab_user(), bookmarklet_from=bookmarklet_from, create=True, edit=False)

@embed_blueprint.route('/check.json')
def check_json():
    url = request.args.get('url')
    if not url:
        return jsonify(error=True, message=gettext("No URL provided"), url=url)
    if not url.startswith(('http://', 'https://')):
        return jsonify(error=True, message=gettext("URL doesn't start by http:// or https://"), url=url)
    
    if url == 'http://':
        return jsonify(error=False, url=url)

    sg_link = find_smartgateway_link(url, request.referrer)
    if sg_link:
        return jsonify(error=False, sg_link=sg_link, url=url)
    
    metadata = get_url_metadata(url, timeout = 5)
    if metadata['error_retrieving']:
        return jsonify(error=True, message=gettext("Error retrieving URL"), url=url)

    if metadata['code'] != 200:
        return jsonify(error=True, message=gettext("Error accessing to the URL"), url=url)

    if metadata['x_frame_options'] in ('deny', 'sameorigin') or metadata['x_frame_options'].startswith('allow'):
        return jsonify(error=True, message=gettext("This website does not support being loaded from a different site, so it is unavailable for Go-Lab"), url=url)
    
    if 'html' not in metadata['content_type']:
        if 'shockwave' in metadata['content_type'] or 'flash' in metadata['content_type']:
            return jsonify(error=False, url=url)

        return jsonify(error=True, message=gettext("URL is not HTML"), url=url)

    return jsonify(error=False, url=url, name = metadata['name'], description = metadata['description'])

@embed_blueprint.route('/edit/<identifier>/', methods = ['GET', 'POST'])
@requires_golab_login
def edit(identifier):
    existing_languages = {
        # lang: {
        #     'code': 'es',
        #     'name': 'Spanish',
        #     'url': 'http://....'
        # }
    }
    existing_languages_db = {
        # lang: db_instance
    }
    all_languages = list_of_languages()
    
    # Obtain from the database
    application = db.session.query(EmbedApplication).filter_by(identifier = identifier).first()
    if application is None:
        return "Application does not exist", 404

    for translation in application.translations:
        existing_languages_db[translation.language] = translation
        existing_languages[translation.language] = {
            'code': translation.language,
            'name': all_languages.get(translation.language) or 'Language not supported anymore',
            'url': translation.url
        }
    
    # languages added by the UI
    posted_languages = {
        # 'es' : 'http://.../'
    }

    if request.method == 'POST':
        for key in request.form:
            if key.startswith('language.'):
                lang_code = key[len('language.'):]
                if lang_code in all_languages:
                    posted_languages[lang_code] = request.form[key]
                

    form = ApplicationForm(obj=application)
    if form.validate_on_submit():
        # Check for new ones or changed
        for posted_language, url in posted_languages.items():
            if posted_language in existing_languages_db:
                translation = existing_languages_db[posted_language]
                if translation.url != url: # Don't trigger unnecessary UPDATEs
                    translation.url = url
            else:
                translation = EmbedApplicationTranslation(embed_application = application, url=url, language=posted_language)
                db.session.add(translation)

        # Delete old ones
        for existing_language, translation in existing_languages_db.items():
            if existing_language not in posted_languages:
                existing_languages.pop(existing_language)
                db.session.delete(translation)

        form_scale = _get_scale_value(form)
        application.update(url=form.url.data, name=form.name.data, height=form.height.data, scale=form_scale, age_ranges_range=form.age_ranges_range.data, description=form.description.data, domains_text=form.domains_text.data)
        db.session.commit()
    
        # TODO: does this still make sense?
        # if request.form.get('action') == 'publish':
        #     return _post_contents(app_to_json(application), application.url)

    # Add the posted languages to the existing ones
    for lang_code, url in posted_languages.items():
        existing_languages[lang_code] = {
            'code' : lang_code,
            'name' : all_languages[lang_code],
            'url' : url
        }

    # Obtain the languages formatted as required but excluding those already added
    languages = obtain_formatted_languages(existing_languages)
    bookmarklet_from = request.args.get('url')
    return render_template("embed/create.html", user = current_golab_user(), form=form, identifier=identifier, header_message=gettext("Edit web"), languages=languages, existing_languages=list(existing_languages.values()), all_languages=all_languages, bookmarklet_from=bookmarklet_from, edit=True, create=False)

from labmanager.views.repository import app_to_json
