from sys import modules

from yaml import load as yload

from flask import redirect, url_for, abort

from flask.ext import wtf
from flask.ext.admin import Admin, BaseView, expose, AdminIndexView
from flask.ext.admin.model import InlineFormAdmin
from flask.ext.admin.contrib.sqlamodel import ModelView

from labmanager.models import LabManagerUser as User
from labmanager.models import NewLMS, Permission, Experiment, NewRLMS, Credential, NewCourse
from labmanager.database import db_session as DBS

configs = yload(open('labmanager/config.yaml'))

class PermissionPanel(ModelView):
    form_columns = ('newlms','newcourse','experiment','resource_link_id','configuration','access')
    sel_choices = [(status, status.title()) for status in configs['permission_status']]
    form_overrides = dict(access=wtf.SelectField)
    form_args = dict(
        access=dict( choices=sel_choices )
        )

class LabmanagerUser(ModelView):

    form_columns = ('name', 'login', 'password', 'access_level')
    sel_choices = [(level, level.title()) for level in configs['user_access_level']]
    form_overrides = dict(access_level=wtf.SelectField)
    form_args = dict(
        access_level=dict( choices=sel_choices )
        )

class CredentialForm(InlineFormAdmin):
    form_columns = ('id','kind', 'key', 'secret')
    excluded_form_fields = ('id')

    def postprocess_form(self, form):
        sel_choices =  [ (x , x.title()) for x in configs['authentication_types']]
        form.kind = wtf.SelectField(u'Kind', choices=sel_choices)
        return form

class LMSPanel(ModelView):
    inline_models = (CredentialForm(Credential),)

    def is_accessible(self):
        return True

class RLMSPanel(ModelView):
    form_columns = ('kind', 'location', 'url')
    column_exclude_list = ('version')
    sel_choices = []
    for ins_rlms in configs['installed_rlms']:
        for ver in configs['installed_rlms'][ins_rlms]:
            sel_choices.append(("%s<>%s" % (ins_rlms, ver),"%s - %s" % (ins_rlms.title(), ver)) )
    form_overrides = dict(kind=wtf.SelectField)
    form_args = dict(
        kind=dict( choices=sel_choices )
        )

    def on_model_change(self, form, model):
        rlms_ver = model.kind.split('<>')
        model.kind, model.version = rlms_ver[0], rlms_ver[1]
        pass

    def is_accesible(self):
        return True

class AdminPanel(AdminIndexView):
    def is_accessible(self):
        return True

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
        return redirect('/admin')

def init_admin(labmanager, db_session):
    admin = Admin(index_view = AdminPanel(), name='LabManager')

    admin.add_view(PermissionPanel(Permission, session=db_session, name='Permissions'))

    admin.add_view(LMSPanel(NewLMS, session=db_session, category='LMS', name='LMS'))
    admin.add_view(ModelView(NewCourse, session=db_session, category='LMS', name='Courses'))

    admin.add_view(RLMSPanel(NewRLMS, session=db_session, category='ReLMS', name='RLMS'))

    admin.add_view(ModelView(Experiment, session=db_session, category='ReLMS', name='Experiments'))

    admin.add_view(LabmanagerUser(User, session=db_session, name='Users'))

    admin.init_app(labmanager)
