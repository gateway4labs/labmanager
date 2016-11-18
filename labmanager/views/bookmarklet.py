from flask import Blueprint, request, url_for, redirect, render_template

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
    url = request.args.get('url')
    return redirect(url_for('embed.create', url=url))

