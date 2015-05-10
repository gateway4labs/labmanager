# -*-*- encoding: utf-8 -*-*-
#
# gateway4labs is free software: you can redistribute it and/or modify
# it under the terms of the BSD 2-Clause License
# gateway4labs is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

from flask import url_for, Markup, request
from flask.ext.admin import Admin, AdminIndexView, expose
from flask.ext.admin.contrib.sqlamodel import ModelView
from labmanager.models import Laboratory, RLMS
from labmanager.views import RedirectView
from labmanager.rlms import get_manager_class, Capabilities
from labmanager.babel import lazy_gettext, gettext
from labmanager.db import db
 
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
    return Markup('<a href="%s">%s</a>' % (url_for('.list_widgets', public_identifier = public_id_formatter(v, c, laboratory, p)), gettext("list")))

def rlms_formatter(v, c, laboratory, p):
    rlms = laboratory.rlms
    return Markup('<a href="%s">%s - %s</a> (%s)' % (rlms.url, rlms.kind, rlms.version, rlms.location))

class PublicLaboratoriesPanel(ModelView):
    can_delete = False
    can_edit   = False
    can_create = False
    column_list = ('rlms', 'name', 'laboratory_id', 'public_identifier', 'widgets')
    column_labels = dict(rlms=lazy_gettext('rlms'), name=lazy_gettext('name'), laboratory_id=lazy_gettext('laboratory_id'), public_identifier=lazy_gettext('public_identifier'), widgets=lazy_gettext('widgets'))
    column_formatters = dict( rlms = rlms_formatter, local_identifier = public_id_formatter, widgets = list_widgets_formatter )

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
        RLMS_CLASS = get_manager_class(rlms_db.kind, rlms_db.version, rlms_db.id)
        rlms = RLMS_CLASS(rlms_db.configuration)
        if Capabilities.WIDGET in rlms.get_capabilities():
            widgets = rlms.list_widgets(laboratory.laboratory_id)
        else:
            widgets = [ { 'name' : 'lab', 'description' : 'Main view of the laboratory' } ]
       
        autoload = rlms_db.default_autoload

        links = {
            # widget-name : link
        }
        for widget in widgets:
            link = url_for('opensocial.public_widget_xml', lab_name = public_identifier, widget_name = widget['name'], _external = True)
            if link.startswith('https://'):
                link = link.replace('https://', 'http://', 1)
            links[widget['name']] = link

        list_widgets_kwargs = dict(public_identifier = public_identifier, _external = True)
        return self.render("public/list_widgets.html", list_widgets_kwargs = list_widgets_kwargs, widgets = widgets, lab_name = public_identifier, links = links, autoload = autoload)

def list_labs_formatter(v, c, rlms, p):
    return Markup('<a href="%s">%s</a>' % (url_for('.list_labs', public_identifier = rlms.public_identifier), gettext("list")))

def public_rlms_formatter(v, c, rlms, p):
    return Markup('<a href="%s">%s</a>' % (rlms.url, rlms.get_name()))

class PublicSystemsPanel(ModelView):
    can_delete = False
    can_edit   = False
    can_create = False
    column_list = ('rlms', 'location', 'labs')
    column_labels  = dict(kind=lazy_gettext('rlms'), labs=lazy_gettext('labs'))
    column_formatters = dict( labs = list_labs_formatter, rlms = public_rlms_formatter )

    def __init__(self, session, **kwargs):
        super(PublicSystemsPanel, self).__init__(RLMS, session, **kwargs)

    def get_query(self, *args, **kwargs):
        query_obj = super(PublicSystemsPanel, self).get_query(*args, **kwargs)
        query_obj = query_obj.filter_by(publicly_available = True)
        return query_obj

    def get_count_query(self, *args, **kwargs):
        query_obj = super(PublicSystemsPanel, self).get_count_query(*args, **kwargs)
        query_obj = query_obj.filter_by(publicly_available = True)
        return query_obj

    @expose("/labs/<public_identifier>/")
    def list_labs(self, public_identifier):
        rlms_db = self.session.query(RLMS).filter_by(public_identifier = public_identifier, publicly_available = True).first()
        if rlms_db is None:
            return self.render("public/errors.html", message = "RLMS not found")

        RLMS_CLASS = get_manager_class(rlms_db.kind, rlms_db.version, rlms_db.id)
        rlms = RLMS_CLASS(rlms_db.configuration)

        query = request.args.get('q')
        if query is not None:
            page = request.args.get('p', '1')
            try:
                page = int(page)
            except:
                page = 1
        else:
            page = 1

        RLMS_CLASS = get_manager_class(rlms_db.kind, rlms_db.version, rlms_db.id)
        rlms = RLMS_CLASS(rlms_db.configuration)
        if query:
            query_results = rlms.search(query = query, page = page)
            labs = query_results['laboratories']
            force_search = False
            number_of_pages = query_results.get('pages', 1)
            pages = []
            if number_of_pages > 1:
                for p in xrange(1, number_of_pages + 1):
                    obj = {
                        'label' : unicode(p),
                        'link'  : url_for('.list_labs', public_identifier = public_identifier, q = query, p = p)
                    }
                    obj['active'] = (p != page)
                    pages.append(obj)
        else:
            query_results = {}
            labs = rlms.get_laboratories()
            capabilities = rlms.get_capabilities()
            force_search = Capabilities.FORCE_SEARCH in capabilities
            pages = []

        return self.render("public/list_labs.html", rlms = rlms_db, labs = labs, query = query, force_search = force_search, pages = pages, page = page, public_identifier = public_identifier)


    @expose("/system/<rlms_identifier>/widgets/<quoted_url:lab_identifier>/")
    def list_widgets(self, rlms_identifier, lab_identifier):
        rlms_db = self.session.query(RLMS).filter_by(public_identifier = rlms_identifier, publicly_available = True).first()
        if rlms_db is None:
            return self.render("public/errors.html", message = "RLMS not found")

        RLMS_CLASS = get_manager_class(rlms_db.kind, rlms_db.version, rlms_db.id)
        rlms = RLMS_CLASS(rlms_db.configuration)

        if Capabilities.WIDGET in rlms.get_capabilities():
            widgets = rlms.list_widgets(lab_identifier)
        else:
            widgets = [ { 'name' : 'lab', 'description' : 'Main view of the laboratory' } ]

        autoload = rlms_db.default_autoload

        # XXX: TODO: check if the lab_identifier does not exist and report it!
        links = {
            # widget-name : link
        }
        for widget in widgets:
            link = url_for('opensocial.public_rlms_widget_xml', rlms_identifier = rlms_identifier, lab_name = lab_identifier, widget_name = widget['name'], _external = True)
            if link.startswith('https://'):
                link = link.replace('https://', 'http://', 1)
            links[widget['name']] = link

        list_widgets_kwargs = dict(rlms_identifier = rlms_identifier, lab_identifier = lab_identifier, _external = True)
        return self.render("public/list_widgets.html", list_widgets_kwargs = list_widgets_kwargs, widgets = widgets, lab_name = lab_identifier, links = links, autoload = autoload)


############################################## 
# 
#    Initialization
# 

def init_public_admin(app):
    public_admin_url = '/public'
    public_admin = Admin(index_view = PublicAdminPanel(url=public_admin_url, endpoint = 'public_admin'), name = lazy_gettext(u"Public laboratories"), url = public_admin_url, endpoint = 'public-admin')
    public_admin.add_view(PublicSystemsPanel( db.session, name = lazy_gettext(u"Show public systems"), endpoint = 'public_admin_systems', url = 'systems/public'))
    public_admin.add_view(PublicLaboratoriesPanel( db.session, name = lazy_gettext(u"Show public labs"), endpoint = 'public_admin_labs', url = 'labs/public'))
    public_admin.add_view(RedirectView('index', name = lazy_gettext(u"Back"), endpoint = 'public_admin_logout', url = 'back'))
    public_admin.init_app(app)
