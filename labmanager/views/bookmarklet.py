from flask import Blueprint, request, url_for, redirect

bookmarklet_blueprint = Blueprint('bookmarklet', __name__)

@bookmarklet_blueprint.route('/')
def index():
    return ":-)"

@bookmarklet_blueprint.route('/create')
def create():
    url = request.args.get('url')
    return redirect(url_for('embed.create', url=url))

