import sys
from flask import redirect, url_for, abort
from flask.ext.admin import Admin, BaseView, expose, AdminIndexView
from flask.ext.admin.contrib.sqlamodel import ModelView
from labmanager.models import LabManagerUser as User
from labmanager.models import NewLMS, Permission, Experiment, NewRLMS, Credential, NewCourse
from labmanager.database import db_session as DBS

class RLMSPanel(ModelView):
    def is_accesible(self):
        return True

class LMSPanel(ModelView):
    inline_models = (Credential,)
    def is_accessible(self):
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
            model_class = reduce(getattr, model.split("."), sys.modules[__name__])
            info = DBS.query(model_class).filter_by(id = r_id).first()
            response = self.render('admin/models/show.html', info=info.__dict__)
        except AttributeError:
            response = abort(404)
        return response

    @expose('/Permission/<int:id>/update/<status>')
    def update(self, id, status):
        Permission.find(id).change_status(status)
        return redirect('/admin')

def init_admin(labmanager, db_session):
    admin = Admin(index_view = AdminPanel(), name='LabManager')

    admin.add_view(ModelView(Permission, session=db_session, name='Permissions'))
    admin.add_view(ModelView(Experiment, session=db_session, name='Experiments'))

    admin.add_view(LMSPanel(NewLMS, session=db_session, category='Admin', name='LMS'))
    admin.add_view(ModelView(NewCourse, session=db_session, category='Admin', name='Courses'))
    admin.add_view(ModelView(NewRLMS, session=db_session, category='Admin', name='RLMS'))
    admin.add_view(ModelView(User, session=db_session, category='Admin', name='Users'))

    admin.init_app(labmanager)
