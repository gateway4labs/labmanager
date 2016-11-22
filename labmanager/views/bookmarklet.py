from flask import Blueprint, request, url_for, redirect, render_template

from labmanager.db import db
from labmanager.models import RLMS, Laboratory
from labmanager.rlms import Capabilities

bookmarklet_blueprint = Blueprint('bookmarklet', __name__)

@bookmarklet_blueprint.route('/')
def index():
    if ' Edge/' in request.headers.get('User-Agent', ''):
        browser = 'edge'
    else:
        browser = request.user_agent.browser
    return render_template("bookmarklet/index.html", browser=browser)

@bookmarklet_blueprint.route('/create')
def create():
    url = request.args.get('url') or ''
    
    rlms_by_id = {}
    for db_rlms in db.session.query(RLMS).filter_by(publicly_available=True).all():
        rlms = db_rlms.get_rlms()
        rlms_by_id[db_rlms.id] = rlms
        if Capabilities.URL_FINDER in rlms.get_capabilities():
            base_urls = rlms.get_base_urls() or []
            for base_url in base_urls:
                if url.startswith(base_url):
                    lab = rlms.get_lab_by_url(url)
                    if lab is not None:
                        return redirect(url_for('.public_rlms', rlms_type=db_rlms.kind, lab_name=lab.laboratory_id))

    for db_rlms in db.session.query(RLMS).filter_by(publicly_available=False).all():
        rlms = db_rlms.get_rlms()
        rlms_by_id[db_rlms.id] = rlms
        if Capabilities.URL_FINDER in rlms.get_capabilities():
            base_urls = rlms.get_base_urls() or []
            for base_url in base_urls:
                if url.startswith(base_url):
                    lab = rlms.get_lab_by_url(url)
                    db_lab = db.session.query(Laboratory).filter_by(rlms=db_rlms, laboratory_id=lab.laboratory_id, publicly_available=True).first()
                    if db_lab is not None:
                        return redirect(url_for('.public_lab', lab_identifier=db_lab.public_identifier))

    return redirect(url_for('embed.create', url=url))

@bookmarklet_blueprint.route('/pub/rlms/<rlms_type>/<path:lab_name>')
def public_rlms(rlms_type, lab_name):
    return ":-)"
    
@bookmarklet_blueprint.route('/pub/lab/<path:lab_identifier>')
def public_lab(lab_identifier):
    return ":-)"

