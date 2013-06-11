# -*-*- encoding: utf-8 -*-*-
from hashlib import new as new_hash
from sys import modules
from yaml import load as yload

from wtforms.fields import PasswordField

from flask import redirect, abort, session
from flask.ext import wtf
from flask.ext.admin import expose

from labmanager.views.admin import L4lModelView, L4lAdminIndexView
# LMS, Laboratory and Course declarations are needed for the 'show' view
# so that sys.modules[__name__] can find it and create the Class object
# TODO: clean up this part
from labmanager.models import PermissionToCourse, LMS, Laboratory, Course
from labmanager.models import LabManagerUser, LmsUser
from labmanager.database import db_session as DBS

config = yload(open('labmanager/config.yml'))

class AdminPanel(L4lAdminIndexView):
    @expose('/')
    def index(self):
        pending_requests = PermissionToCourse.find_by_status(u'pending')
        data = {
            'requests' : pending_requests,
            'current_user' : LabManagerUser.find(session.get('user_id'))
        }
        return self.render('l4l-admin/index.html', info=data)

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

            response = self.render('l4l-admin/models/show.html', info=data)
        except AttributeError:
            response = abort(404)
        return response

    @expose('/Permission/<int:id>/update/<status>')
    def update(self, id, status):
        PermissionToCourse.find(id).change_status(status)
        return redirect('/admin') # redirect to index

class UsersPanel(L4lModelView):

    column_list = ('login', 'name')

    def __init__(self, session, **kwargs):
        super(UsersPanel, self).__init__(LabManagerUser, session, **kwargs)

    form_columns = ('name', 'login', 'password')
    form_overrides = dict(access_level=wtf.SelectField, password=PasswordField)

    def on_model_change(self, form, model):
        model.password = new_hash("sha", model.password).hexdigest()

class LmsUsersPanel(L4lModelView):

    column_list = ('lms', 'login', 'full_name', 'access_level')

    def __init__(self, session, **kwargs):
        super(LmsUsersPanel, self).__init__(LmsUser, session, **kwargs)

    form_columns = ('full_name', 'login', 'password', 'access_level', 'lms')
    sel_choices = [(level, level.title()) for level in config['user_access_level']]
    form_overrides = dict(access_level=wtf.SelectField, password=PasswordField)
    form_args = dict( access_level=dict( choices=sel_choices ) )

    def on_model_change(self, form, model):
        # TODO: don't update password always
        model.password = new_hash("sha", model.password).hexdigest()

