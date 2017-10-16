import requests
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

@stats_blueprint.route("/monthly")
def monthly():
    try:
        failure_data = requests.get("http://composer.golabz.eu/translator/stats/status.json").json()
    except:
        failure_data = {
            'failing': [],
            'flash': [],
            'ssl': [],
        }

    lab_contents = requests.get('http://www.golabz.eu/rest/labs/retrieve.json').json()
    lab_per_url = {
        # url: lab_data
    }
    for lab in lab_contents:
        for lab_app in lab['lab_apps']:
            lab_per_url[lab_app['app_url']] = lab

    month_results = [
        # {
        #    'year': year,
        #    'month': month,
        #    'count': count,
        # }
    ]
    monthly_summary = {
        # (year, month): count
    }
    for count, year, month in db.session.query(func.count("id"), UseLog.year, UseLog.month).group_by(UseLog.year, UseLog.month).all():
        month_results.append({
            'year': year,
            'month': month,
            'count': count
        })
        monthly_summary[year, month] = count
    month_results.sort(lambda x, y: cmp(x['year'], y['year']) or cmp(x['month'], y['month']), reverse=True)

    temporal_month_url = {
        # (year, month): [ { 'count': count, 'url': url ]
    }
    for count, year, month, url in db.session.query(func.count("id"), UseLog.year, UseLog.month, UseLog.url).group_by(UseLog.year, UseLog.month, UseLog.url).all():
        if (year, month) not in temporal_month_url:
            temporal_month_url[year, month] = []

        temporal_month_url[year, month].append({
            'count': count,
            'url': url,
            'data': lab_per_url.get(url, {})
        })
        temporal_month_url[year, month].sort(lambda x, y: cmp(x['count'], y['count']), reverse=True)

    month_url_results = [
        # {
        #    'year': year,
        #    'month': month,
        #    'urls': [
        #      { # sorted > to min
        #        'count': count,
        #        'url': url
        #      }
        #    ]
        # }
    ]
    for (year, month), results in temporal_month_url.items():
        month_url_results.append({
            'year': year,
            'month': month,
            'count': monthly_summary[year, month],
            'urls': results,
        })

    month_url_results.sort(lambda x, y: cmp(x['year'], y['year']) or cmp(x['month'], y['month']), reverse=True)
    return render_template("stats/monthly.html", month_results=month_results, month_url_results=month_url_results, failure_data=failure_data)


