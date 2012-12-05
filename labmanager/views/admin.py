import sys
from flask import redirect, url_for, abort
from flask.ext.superadmin import Admin, BaseView, expose, AdminIndexView
from flask.ext.superadmin.contrib import sqlamodel
from labmanager.models import NewLMS, Permission, Experiment, NewRLMS, Credential
from labmanager.database import db_session as DBS


class RLMSPanel(sqlamodel.ModelAdmin):
    def is_accessible(self):
        return True

class LMSPanel(sqlamodel.ModelAdmin):
    def is_accessible(self):
        return True

#Create the Admin Views
class AdminPanel(AdminIndexView):
    def is_accessible(self):
        return True

    @expose('/')
    def index(self):
        pending_requests = Permission.find_by_status('pending')
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
        return redirect('/admin/')

def init_admin(self, db_session):
    admin = Admin(index_view = AdminPanel())
    
    lmspanel = LMSPanel(NewLMS, session = db_session)
    admin.add_view(lmspanel)
    
    rlmspanel = RLMSPanel(NewRLMS, session = db_session)
    admin.add_view(rlmspanel)

    experimentpanel = RLMSPanel(Experiment, session = db_session)
    admin.add_view(experimentpanel)

    admin.register(Permission, session = db_session)
    admin.register(Credential, session = db_session)

    admin.init_app(self)
