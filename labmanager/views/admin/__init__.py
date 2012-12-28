# -*-*- encoding: utf-8 -*-*-

from flask import request, redirect, url_for
from flask.ext.login import current_user
from flask.ext.admin.contrib.sqlamodel import ModelView

class L4lModelView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated()
    
    def _handle_view(self, name, **kwargs):
        if not self.is_accessible():
            return redirect(url_for('login', next=request.url))

        return super(L4lModelView, self)._handle_view(name, **kwargs)
