# -*-*- encoding: utf-8 -*-*-
#
# gateway4labs is free software: you can redistribute it and/or modify
# it under the terms of the BSD 2-Clause License
# gateway4labs is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

from flask import url_for, Markup

from flask.ext.admin import Admin, AdminIndexView, expose
from flask.ext.admin.contrib.sqlamodel import ModelView

from labmanager.models import Laboratory
from labmanager.views import RedirectView
from labmanager.rlms import get_manager_class
from labmanager.babel import gettext, ngettext, lazy_gettext
 
##############################################
# 
#    Index
# 


class PublicAdminPanel(AdminIndexView):
    @expose()
    def index(self):
        return self.render("public/index.html")


###############################################
# 
#   Laboratories
# 

def public_id_formatter(v, c, laboratory, p):
    return laboratory.public_identifier or 'N/A'

def list_widgets_formatter(v, c, laboratory, p):
    return Markup('<a href="%s">list</a>' % url_for('.list_widgets', public_identifier = public_id_formatter(v, c, laboratory, p)))

class PublicLaboratoriesPanel(ModelView):

    can_delete = False
    can_edit   = False
    can_create = False

    column_list = ('rlms', 'name', 'laboratory_id', 'public_identifier', 'widgets')
    column_labels = dict(rlms=lazy_gettext('rlms'), name=lazy_gettext('name'), laboratory_id=lazy_gettext('laboratory_id'), public_identifier=lazy_gettext('public_identifier'), widgets=lazy_gettext('widgets'))
    column_formatters = dict( local_identifier = public_id_formatter, widgets = list_widgets_formatter )

    def __init__(self, session, **kwargs):
        super(PublicLaboratoriesPanel, self).__init__(Laboratory, session, **kwargs)

    def get_query(self, *args, **kwargs):
        query_obj = super(PublicLaboratoriesPanel, self).get_query(*args, **kwargs)
        query_obj = query_obj.filter_by(publicly_available = True)
        return query_obj

    def get_count_query(self, *args, **kwargs):
        query_obj = super(PublicLaboratoriesPanel, self).get_count_query(*args, **kwargs)
        query_obj = query_obj.filter_by(publicly_available = True)
        return query_obj

    @expose("/widgets/<public_identifier>/")
    def list_widgets(self, public_identifier):
        laboratory = self.session.query(Laboratory).filter_by(public_identifier = public_identifier, publicly_available = True).first()
        if laboratory is None:
            return self.render("public/errors.html", message = "Laboratory not found")

        rlms_db = laboratory.rlms
        RLMS_CLASS = get_manager_class(rlms_db.kind, rlms_db.version)
        rlms = RLMS_CLASS(rlms_db.configuration)

        widgets = rlms.list_widgets(laboratory.laboratory_id)
        return self.render("public/list_widgets.html", widgets = widgets, lab_name = public_identifier)

############################################## 
# 
#    Initialization
# 
def init_public_admin(app, db_session):
    public_admin_url = '/public'
    public_admin = Admin(index_view = PublicAdminPanel(url=public_admin_url, endpoint = 'public_admin'), name = u"Public labs", url = public_admin_url, endpoint = 'public-admin')
    public_admin.add_view(PublicLaboratoriesPanel( db_session, name = u"Public labs", endpoint = 'public_admin_labs', url = 'labs/public'))

    public_admin.add_view(RedirectView('index',          name = u"Back", endpoint = 'public_admin_logout', url = 'back'))
    public_admin.init_app(app)

