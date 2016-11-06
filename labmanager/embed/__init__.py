import traceback
from flask import Blueprint, render_template, make_response, redirect, url_for, request
from labmanager.views.authn import requires_siway_login, current_siway_user

from labmanager.db import db
from labmanager.babel import gettext, lazy_gettext
from labmanager.models import EmbedApplication, EmbedApplicationTranslation
from labmanager.translator.languages import obtain_languages

from flask.ext.wtf import Form
from wtforms import TextField, HiddenField, SelectMultipleField
from wtforms.validators import required
from wtforms.fields.html5 import URLField
from wtforms.widgets import HiddenInput, TextInput, CheckboxInput, html_params, HTMLString
from wtforms.widgets.html5 import URLInput

embed_blueprint = Blueprint('embed', __name__)

@embed_blueprint.context_processor
def inject_variables():
    return dict(current_siway_user=current_siway_user())

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

# 
# Public URLs
# 

@embed_blueprint.route('/apps/')
def apps():
    applications = db.session.query(EmbedApplication).order_by(EmbedApplication.last_update).all()
    return render_template("embed/apps.html", user = current_siway_user(), applications = applications, title = gettext("List of applications"))

@embed_blueprint.route('/apps/<identifier>/')
def app(identifier):
    application = db.session.query(EmbedApplication).filter_by(identifier = identifier).first()
    if application is None:
        return render_template("embed/error.html", message = gettext("Application '{identifier}' not found").format(identifier=identifier), user = current_siway_user()), 404

    return render_template("embed/app.html", user = current_siway_user(), app = application, title = gettext("Application {name}").format(name=application.name))

@embed_blueprint.route('/apps/<identifier>/app.xml')
def app_xml(identifier):
    application = db.session.query(EmbedApplication).filter_by(identifier = identifier).first()
    if application is None:
        return render_template("embed/error.xml", user = current_siway_user(), message = gettext("Application '{identifier}' not found").format(identifier=identifier)), 404

    apps_per_language = {}
    languages = ['en']
    for translation in application.translations:
        apps_per_language[translation.language] = translation.url
        languages.append(translation.language)

    author = application.owner.full_name

    response = make_response(render_template("embed/app.xml", author = author, user = current_siway_user(), identifier=identifier, app = application, languages=languages, apps_per_language = apps_per_language, title = gettext("Application {name}").format(name=application.name)))
    response.content_type = 'application/xml'
    return response

# 
# Management URLs
# 

@embed_blueprint.route('/')
@requires_siway_login
def index():
    applications = db.session.query(EmbedApplication).filter_by(owner = current_siway_user()).order_by(EmbedApplication.last_update).all()
    return render_template("embed/index.html", applications = applications, user = current_siway_user())

AGE_RANGES = ['<6', '6-8', '8-10', '10-12', '12-14', '14-16', '16-18', '>18']

class ApplicationForm(Form):
    name = TextField(lazy_gettext("Name:"), validators=[required()], widget = AngularJSTextInput(ng_enter="submitForm()"), description=lazy_gettext("Name of the resource"))
    url = URLField(lazy_gettext("Web:"), validators=[required()], widget = AngularJSURLInput(ng_model='embed.url', ng_enter="submitForm()"), description=lazy_gettext("Web address of the resource"))
    # age_ranges = MultiCheckboxField(lazy_gettext("Age ranges:"), choices=zip(AGE_RANGES, AGE_RANGES), description=lazy_gettext("Select the age ranges this tool is useful for"))
    age_ranges_range = HiddenField(lazy_gettext("Age ranges:"), validators=[required()], description=lazy_gettext("Select the age ranges this tool is useful for"))
    description = TextField(lazy_gettext("Description:"), validators=[required()], widget = AngularJSTextInput(ng_enter="submitForm()"), description=lazy_gettext("Describe the resource in a few words"))
    domains_text = TextField(lazy_gettext("Domains:"), validators=[required()], widget = AngularJSTextInput(ng_enter="submitForm()"), description=lazy_gettext("Say in which domains apply to the resource (separated by commas): e.g., physics, electronics..."))
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

@embed_blueprint.route('/create', methods = ['GET', 'POST'])
@requires_siway_login
def create():
    form = ApplicationForm()
    if form.validate_on_submit():
        form_scale = _get_scale_value(form)
        application = EmbedApplication(url = form.url.data, name = form.name.data, owner = current_siway_user(), height=form.height.data, scale=form_scale, description=form.description.data, age_ranges = form.age_ranges_range.data)
        application.domains_text = form.domains_text.data
        db.session.add(application)
        try:
            db.session.commit()
        except Exception as e:
            traceback.print_exc()
            return render_template("embed/error.html", message = gettext("There was an error creating an application"), user = current_siway_user()), 500
        else:
            return redirect(url_for('.edit', identifier=application.identifier))
            
    return render_template("embed/create.html", form=form, header_message=gettext("Add a web"), user = current_siway_user())

@embed_blueprint.route('/edit/<identifier>/', methods = ['GET', 'POST'])
@requires_siway_login
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

    # Add the posted languages to the existing ones
    for lang_code, url in posted_languages.items():
        existing_languages[lang_code] = {
            'code' : lang_code,
            'name' : all_languages[lang_code],
            'url' : url
        }

    # Obtain the languages formatted as required but excluding those already added
    languages = obtain_formatted_languages(existing_languages)
    return render_template("embed/create.html", user = current_siway_user(), form=form, identifier=identifier, header_message=gettext("Edit web"), languages=languages, existing_languages=list(existing_languages.values()), all_languages=all_languages)

