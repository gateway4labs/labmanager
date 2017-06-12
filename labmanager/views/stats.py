from flask import render_template, Blueprint, current_app, request

from sqlalchemy import func

from labmanager.db import db
from labmanager.models import UseLog

stats_blueprint = Blueprint('stats', __name__)

@stats_blueprint.before_request
def check_auth():
    key = request.args.get("key")
    if not key:
        return "key missing"

    if key != current_app.config.get("EASYADMIN_KEY"):
        return "Invalid key"
    return 

@stats_blueprint.route("/")
def simple():
    by_day = sorted(db.session.query(func.count("*"), UseLog.date).group_by(UseLog.date).all(), lambda x, y: cmp(x[1], y[1]))
    return render_template("stats/index.html", by_day = by_day)
