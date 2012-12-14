# -*-*- encoding: utf-8 -*-*-
from sys import modules
from yaml import load as yload

from flask import redirect, abort
from flask.ext import wtf
from flask.ext.login import current_user
from flask.ext.admin import expose, AdminIndexView
from flask.ext.admin.contrib.sqlamodel import ModelView

from labmanager.models import Permission
from labmanager.models import LabManagerUser as User
from labmanager.database import db_session as DBS

config = yload(open('labmanager/config.yaml'))

class AdminPanel(AdminIndexView):
    def is_accessible(self):
        return current_user.is_authenticated()

    @expose('/')
    def index(self):
        pending_requests = Permission.find_by_status(u'pending')
        data = {'requests' : pending_requests }
        return self.render('admin/index.html', info=data)

    @expose('/<model>/<int:r_id>/show')
    def show(self, model ,r_id):
        response = ""
        try:
            model_class = reduce(getattr, model.split("."), modules[__name__])
            info = DBS.query(model_class).filter_by(id = r_id).first()
            data = {}
            for col in info.__table__.columns:
                col = str(col)
                col_name = col[col.find('.') + 1:]
                data[col_name] = info.__dict__[col_name]

            response = self.render('admin/models/show.html', info=data)
        except AttributeError:
            response = abort(404)
        return response

    @expose('/Permission/<int:id>/update/<status>')
    def update(self, id, status):
        Permission.find(id).change_status(status)
        return redirect('/admin') # redirect to index

class UsersPanel(ModelView):
    def __init__(self, session, **kwargs):
        # You can pass name and other parameters if you want to
        default_args = { "name":u"Users" }
        default_args.update(**kwargs)
        super(UsersPanel, self).__init__(User, session, **default_args)

    def is_accessible(self):
        return current_user.is_authenticated()

    form_columns = ('name', 'login', 'password', 'access_level')
    sel_choices = [(level, level.title()) for level in config['user_access_level']]
    form_overrides = dict(access_level=wtf.SelectField)
    form_args = dict(
        access_level=dict( choices=sel_choices )
        )

