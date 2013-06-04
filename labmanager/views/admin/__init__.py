# -*-*- encoding: utf-8 -*-*-

from flask import request, redirect, url_for, session
from flask.ext.login import current_user
from flask.ext.admin import BaseView, AdminIndexView
from flask.ext.admin.contrib.sqlamodel import ModelView

class L4lModelView(ModelView):
    def is_accessible(self):
        if not current_user.is_authenticated():
            return False

        return session['usertype'] == 'labmanager'
    
    def _handle_view(self, name, **kwargs):
        if not self.is_accessible():
            return redirect(url_for('login_admin', next=request.url))

        return super(L4lModelView, self)._handle_view(name, **kwargs)

class L4lBaseView(BaseView):
    def is_accessible(self):
        if not current_user.is_authenticated():
            return False
        
        return session['usertype'] == 'labmanager'
    
    def _handle_view(self, name, **kwargs):
        if not self.is_accessible():
            return redirect(url_for('login_admin', next=request.url))

        return super(L4lBaseView, self)._handle_view(name, **kwargs)

class L4lAdminIndexView(AdminIndexView):
    def is_accessible(self):
        if not current_user.is_authenticated():
            return False
        
        return session['usertype'] == 'labmanager'
    
    def _handle_view(self, name, **kwargs):
        if not self.is_accessible():
            return redirect(url_for('login_admin', next=request.url))

        return super(L4lAdminIndexView, self)._handle_view(name, **kwargs)

