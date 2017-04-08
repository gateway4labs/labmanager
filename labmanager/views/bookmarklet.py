import traceback
import requests
from flask import Blueprint, request, url_for, redirect, render_template, session, current_app

from labmanager.db import db
from labmanager.models import RLMS, Laboratory, EmbedApplication
from labmanager.babel import gettext
from labmanager.rlms import find_smartgateway_link, Capabilities
from labmanager.views.embed import ApplicationForm, SimplifiedApplicationForm, list_of_languages
from labmanager.views.repository import extract_labs, create_lab_id
from labmanager.views.authn import requires_golab_login, current_golab_user

bookmarklet_blueprint = Blueprint('bookmarklet', __name__)

@bookmarklet_blueprint.route('/')
def index():
    if ' Edge/' in request.headers.get('User-Agent', ''):
        browser = 'edge'
    else:
        browser = request.user_agent.browser
    return render_template("bookmarklet/index.html", browser=browser)

@bookmarklet_blueprint.route('/create')
@requires_golab_login
def create():
    url = request.args.get('url') or ''
    
    sg_link = find_smartgateway_link(url, url)
    if sg_link:
        return redirect(sg_link)

    existing_embed_app = db.session.query(EmbedApplication).filter_by(owner=current_golab_user(), url=url).first()
    if existing_embed_app is None:
        return redirect(url_for('embed.create', url=url))
    
    return redirect(url_for('embed.edit', identifier=existing_embed_app.identifier, url=url))

def _return_lab(db_rlms, lab, identifier_links, langs, public_rlms):
    form = SimplifiedApplicationForm()
    form.name.data = lab.name or ''
    form.description.data = lab.description or ''
    # If available, override whatever
    if lab.domains:
        form.domains_text.data = ', '.join(lab.domains or [])
    # If available, override whatever
    if lab.age_ranges:
        form.age_ranges_range.data = EmbedApplication.age_ranges2text(lab.age_ranges or [])
    
    # TODO: does this still make sense?
    if form.validate_on_submit():
        if public_rlms:
            single_lab = None
        else:
            single_lab = lab.laboratory_id
        
        lab_unique_id = create_lab_id(db_rlms, lab.laboratory_id, single = single_lab is not None)
        all_labs = extract_labs(db_rlms, single_lab, fmt='json', 
                        age_ranges=EmbedApplication.text2age_ranges(form.age_ranges_range.data), 
                        domains=form.domains_text.data.split(', '))
        formatted_labs = [ cur_lab for cur_lab in all_labs if cur_lab['id'] == lab_unique_id ]
        if len(formatted_labs) == 0:
            return "Invalid lab identifier"

        # return _post_contents(formatted_labs[0])
        # TODO

    languages = list_of_languages()
    new_langs = []
    for lang in langs:
        lang_name = languages.get(lang)
        if lang_name:
            new_langs.append(lang_name)

    bookmarklet_from = request.args.get('url')

    return render_template("embed/create.html", user = current_golab_user(), form=form, identifier_links=identifier_links, header_message=gettext("View resource"), languages=[], existing_languages=[], all_languages=[], disabled=True, langs = sorted(new_langs), bookmarklet_from=bookmarklet_from, domains_provided=lab.domains is not None, age_ranges_provided=lab.age_ranges is not None)

def _get_widgets(rlms, laboratory_id):
    if Capabilities.WIDGET in rlms.get_capabilities():
        return rlms.list_widgets(laboratory_id)

    return [ { 'name' : 'lab', 'description' : 'Main view of the laboratory' } ]

@bookmarklet_blueprint.route('/pub/rlms/<rlms_id>/<everything:lab_name>', methods=['GET','POST'])
@requires_golab_login
def public_rlms(rlms_id, lab_name):
    db_rlms = db.session.query(RLMS).filter_by(publicly_available=True, public_identifier=rlms_id).first()
    if db_rlms is None:
        return "Laboratory not found", 404
    
    rlms = db_rlms.get_rlms()
    for lab in rlms.get_laboratories():
        if lab.laboratory_id == lab_name:
            widgets = _get_widgets(rlms, lab.laboratory_id)

            links = [] 
            for widget in widgets:
                link = url_for('opensocial.public_rlms_widget_xml', rlms_identifier = rlms_id, lab_name = lab_name, widget_name = widget['name'], _external = True)
                if link.startswith('https://'):
                    link = link.replace('https://', 'http://', 1)

                links.append(link)

            if Capabilities.TRANSLATION_LIST in rlms.get_capabilities():
                langs = (rlms.get_translation_list(lab.laboratory_id) or {}).get('supported_languages') or []
            else:
                langs = []
            return _return_lab(db_rlms, lab, links, langs, public_rlms=True)
    
    return "Laboratory not found", 404

@bookmarklet_blueprint.route('/pub/lab/<everything:public_identifier>', methods=['GET','POST'])
@requires_golab_login
def public_lab(public_identifier):
    db_laboratory = db.session.query(Laboratory).filter_by(publicly_available=True, public_identifier=public_identifier).first()
    if db_laboratory is None:
        return "Laboratory not found", 404

    rlms = db_laboratory.rlms.get_rlms()
    for lab in rlms.get_laboratories():
        if lab.laboratory_id == db_laboratory.laboratory_id:
            widgets = _get_widgets(rlms, lab.laboratory_id)
            links = []
            for widget in widgets:
                link = url_for('opensocial.public_widget_xml', lab_name = public_identifier, widget_name = widget['name'], _external = True)
                if link.startswith('https://'):
                    link = link.replace('https://', 'http://', 1)
                links.append(link)

            if Capabilities.TRANSLATION_LIST in rlms.get_capabilities():
                langs = (rlms.get_translation_list(lab.laboratory_id) or {}).get('supported_languages') or []
            else:
                langs = []
            return _return_lab(db_rlms, lab, links, langs, public_rlms=False)

    return "Laboratory not found", 404


