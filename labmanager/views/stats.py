import requests
from flask import render_template, Blueprint, current_app, request, jsonify

from sqlalchemy import sql
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
    by_day = sorted(session_proxy(db.session.query(func.count("id"), UseLog.date)).group_by(UseLog.date).all(), lambda x, y: cmp(x[1], y[1]))
    return render_template("stats/index.html", by_day = by_day)

def session_proxy(session):
    return session.filter(
                ~sql.and_(UseLog.city == 'Lausanne', UseLog.country == 'CH'),
                ~sql.and_(UseLog.city == 'Enschede', UseLog.country == 'NL'),
                ~sql.and_(UseLog.city == 'Mountain View', UseLog.country == 'US'))

@stats_blueprint.route('/monthly-summary.json')
def monthy_summary_json():
    monthly_summary = [
    ]
    for count, year, month in session_proxy(db.session.query(func.count("id"), UseLog.year, UseLog.month).filter(~UseLog.web_browser.like('%bot%'))).group_by(UseLog.year, UseLog.month).all():
        monthly_summary.append({
            'year': year,
            'month': month,
            'count': count,
        })
    return jsonify(monthly_summary=monthly_summary)


@stats_blueprint.route("/monthly")
def monthly():
    try:
        failure_data = requests.get("https://composer.golabz.eu/translator/stats/status.json").json()
    except:
        failure_data = {
            'failing': [],
            'flash': [],
            'ssl': [],
        }

    lab_contents = requests.get('https://www.golabz.eu/rest/labs/retrieve.json').json()
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
    for count, year, month in session_proxy(db.session.query(func.count("id"), UseLog.year, UseLog.month).filter(~UseLog.web_browser.like('%bot%'))).group_by(UseLog.year, UseLog.month).all():
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
    for count, year, month, url in session_proxy(db.session.query(func.count("id"), UseLog.year, UseLog.month, UseLog.url).filter(~UseLog.web_browser.like('%bot%'))).group_by(UseLog.year, UseLog.month, UseLog.url).all():
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
    return render_template("stats/monthly.html", month_results=month_results, month_url_results=month_url_results, failure_data=failure_data, monthly=True)

@stats_blueprint.route("/yearly")
def yearly():
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
    month = 12
    for count, year in session_proxy(db.session.query(func.count("id"), UseLog.year)).group_by(UseLog.year).all():
        month_results.append({
            'year': year,
            'month': 12,
            'count': count
        })
        monthly_summary[year, month] = count
    month_results.sort(lambda x, y: cmp(x['year'], y['year']) or cmp(x['month'], y['month']), reverse=True)

    temporal_month_url = {
        # (year, month): [ { 'count': count, 'url': url ]
    }
    for count, year, url in session_proxy(db.session.query(func.count("id"), UseLog.year, UseLog.url)).group_by(UseLog.year, UseLog.url).all():
        if (year, 12) not in temporal_month_url:
            temporal_month_url[year, 12] = []

        lab_data = lab_per_url.get(url, {})
        if request.args.get('https') in ['1', 'true'] and lab_data.get('lab_golabz_page') not in failure_data['ssl']:
            continue

        temporal_month_url[year, 12].append({
            'count': count,
            'url': url,
            'data': lab_per_url.get(url, {})
        })
        temporal_month_url[year, 12].sort(lambda x, y: cmp(x['count'], y['count']), reverse=True)

    month_url_results = [
        # {
        #    'year': year,
        #    'month': 12,
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
    return render_template("stats/monthly.html", month_results=month_results, month_url_results=month_url_results, failure_data=failure_data, monthly=False)


