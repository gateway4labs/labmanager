from flask import Blueprint, request, url_for, redirect, render_template

bookmarklet_blueprint = Blueprint('bookmarklet', __name__)

@bookmarklet_blueprint.route('/')
def index():
    return render_template("bookmarklet/index.html")

@bookmarklet_blueprint.route('/create')
def create():
    url = request.args.get('url')
    return redirect(url_for('embed.create', url=url))

