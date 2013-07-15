# -*-*- encoding: utf-8 -*-*-
#
# gateway4labs is free software: you can redistribute it and/or modify
# it under the terms of the BSD 2-Clause License
# gateway4labs is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

import json
import hashlib
import uuid
import traceback
import urlparse
import urllib2

from yaml import load as yload

from wtforms.fields import PasswordField

from flask.ext.wtf import Form, validators, TextField

from flask import request, redirect, url_for, session, Markup, Response

from flask.ext import wtf
from flask.ext.admin import Admin, AdminIndexView, BaseView, expose
from flask.ext.admin.contrib.sqlamodel import ModelView
from flask.ext.login import current_user

from labmanager.scorm import get_scorm_object
from labmanager.models import LmsUser, Course, Laboratory, PermissionToLms, PermissionToLmsUser, PermissionToCourse
from labmanager.views import RedirectView, retrieve_courses
from labmanager.db import db_session
from labmanager.rlms import get_manager_class

config = yload(open('labmanager/config/config.yml'))


#################################################################
# 
#            Base class
# 

class PleAuthManagerMixin(object):
    def is_accessible(self):
        if not current_user.is_authenticated():
            return False

        return session['usertype'] == 'lms' and current_user.access_level == 'admin'
    
class L4lPleModelView(PleAuthManagerMixin, ModelView):

    def _handle_view(self, name, **kwargs):
        if not self.is_accessible():
            return redirect(url_for('login_lms', next=request.url))

        return super(L4lPleModelView, self)._handle_view(name, **kwargs)

class L4lPleAdminIndexView(PleAuthManagerMixin, AdminIndexView):

    def _handle_view(self, name, **kwargs):
        if not self.is_accessible():
            return redirect(url_for('login_lms', next=request.url))

        return super(L4lPleAdminIndexView, self)._handle_view(name, **kwargs)

class L4lPleView(PleAuthManagerMixin, BaseView):
    def __init__(self, session, **kwargs):
        self.session = session
        super(L4lPleView, self).__init__(**kwargs)

    def _handle_view(self, name, **kwargs):
        if not self.is_accessible():
            return redirect(url_for('login_lms', next=request.url))

        return super(L4lPleView, self)._handle_view(name, **kwargs)


##############################################
# 
#    Index
# 


class PleAdminPanel(L4lPleAdminIndexView):
    @expose()
    def index(self):
        return self.render("ple_admin/index.html")


###############################################
# 
#   User management
# 

class PleUsersPanel(L4lPleModelView):

    column_list = ('login', 'full_name', 'access_level')

    form_columns = ('login', 'full_name', 'access_level', 'password')

    sel_choices = [(level, level.title()) for level in config['user_access_level']]

    form_overrides = dict(password=PasswordField, access_level=wtf.SelectField)
    form_args = dict( access_level=dict( choices=sel_choices ) )

    def __init__(self, session, **kwargs):
        super(PleUsersPanel, self).__init__(LmsUser, session, **kwargs)

    def get_query(self, *args, **kwargs):
        query_obj = super(PleUsersPanel, self).get_query(*args, **kwargs)
        query_obj = query_obj.filter_by(lms = current_user.lms)
        return query_obj

    def get_count_query(self, *args, **kwargs):
        query_obj = super(PleUsersPanel, self).get_count_query(*args, **kwargs)
        query_obj = query_obj.filter_by(lms = current_user.lms)
        return query_obj

        

    def on_model_change(self, form, model):
        # TODO: don't update password always
        model.lms   = current_user.lms
        model.password = hashlib.new('sha',model.password).hexdigest()


def create_permission_to_lms_filter(session):
    def filter():
        return session.query(PermissionToLms).filter_by(lms = current_user.lms)

    return staticmethod(filter)

def create_course_filter(session):
    def filter():
        return session.query(Course).filter_by(lms = current_user.lms)

    return staticmethod(filter)

###############################################
# 
#   Laboratories
# 

def local_id_formatter(v, c, laboratory, p):
    for permission in laboratory.lab_permissions:
        if permission.lms == current_user.lms:
            return permission.local_identifier
    return 'N/A'

def list_widgets_formatter(v, c, laboratory, p):
    return Markup('<a href="%s">list</a>' % url_for('.list_widgets', local_identifier = local_id_formatter(v, c, laboratory, p)))


class PleInstructorLaboratoriesPanel(L4lPleModelView):

    can_delete = False
    can_edit   = False
    can_create = False

    column_list = ('rlms', 'name', 'laboratory_id', 'local_identifier', 'widgets')

    column_formatters = dict( local_identifier = local_id_formatter, widgets = list_widgets_formatter )

    def __init__(self, session, **kwargs):
        super(PleInstructorLaboratoriesPanel, self).__init__(Laboratory, session, **kwargs)

    def get_query(self, *args, **kwargs):
        query_obj = super(PleInstructorLaboratoriesPanel, self).get_query(*args, **kwargs)
        query_obj = query_obj.join(PermissionToLms).filter_by(lms = current_user.lms)
        return query_obj

    def get_count_query(self, *args, **kwargs):
        query_obj = super(PleInstructorLaboratoriesPanel, self).get_count_query(*args, **kwargs)
        query_obj = query_obj.join(PermissionToLms).filter_by(lms = current_user.lms)
        return query_obj

    @expose("/widgets/<local_identifier>/")
    def list_widgets(self, local_identifier):
        laboratory = self.session.query(Laboratory).join(PermissionToLms).filter_by(lms = current_user.lms, local_identifier = local_identifier).first()
        if laboratory is None:
            return self.render("ple_admin/errors.html", message = "Laboratory not found")

        rlms_db = laboratory.rlms
        RLMS_CLASS = get_manager_class(rlms_db.kind, rlms_db.version)
        rlms = RLMS_CLASS(rlms_db.configuration)

        widgets = rlms.list_widgets(laboratory.laboratory_id)
        return self.render("ple_admin/list_widgets.html", widgets = widgets, institution_id = current_user.lms.name, lab_name = local_identifier)

#################################################
# 
#   Course management
# 

def format_space_url(v, c, space, p):
    shindig_url = space.lms.shindig_credentials[0]
    # shindig_space_url = '%s/rest/spaces/%s' % (shindig_url, space.context_id)
    # contents = urllib2.urlopen(shindig_space_url).read()
    # return json.loads(contents)['urls'][0]['value']
    return Markup('<a target="_blank" href="https://graasp.epfl.ch/#item=space_%s">link</a>' % space.context_id)

class PleSpacesPanel(L4lPleModelView):

    can_create = can_edit = False

    column_list = ('name', 'context_id', 'url')

    form_columns = ('name', 'context_id')

    column_formatters = dict( url = format_space_url  )

    def __init__(self, session, **kwargs):
        super(PleSpacesPanel, self).__init__(Course, session, **kwargs)

    def get_query(self, *args, **kwargs):
        query_obj = super(PleSpacesPanel, self).get_query(*args, **kwargs)
        query_obj = query_obj.filter_by(lms = current_user.lms)
        return query_obj

    def get_count_query(self, *args, **kwargs):
        query_obj = super(PleSpacesPanel, self).get_count_query(*args, **kwargs)
        query_obj = query_obj.filter_by(lms = current_user.lms)
        return query_obj

    def on_model_change(self, form, model):
        model.lms   = current_user.lms

class SpaceUrlForm(Form):

    url = TextField('Space URL', [validators.Length(min=6, max=200),
                        validators.URL()], description = "Drop here the URL of the Space.", default = "http://graasp.epfl.ch/#item=space_1234")

def create_new_space(numeric_identifier):
    # Retrieve the space name from Shindig
    shindig_url = current_user.lms.shindig_credentials[0].shindig_url
    shindig_space_url = '%s/rest/spaces/%s' % (shindig_url, numeric_identifier)
    shindig_space_contents_json = urllib2.urlopen(shindig_space_url).read()
    shindig_space_contents = json.loads(shindig_space_contents_json)
    space_name = shindig_space_contents['entry']['displayName']

    # Create the space
    context_id = unicode(numeric_identifier)
    course = Course(name = space_name, lms = current_user.lms, context_id = context_id)

    # Add it to the database
    db_session.add(course)
    db_session.commit()

def parse_space_url(url):
    """ Given a Graasp URL, retrieve the space identifier (a number) """
    if 'space_' in url:
        try:
            context_id = int(url.split('space_')[1])
        except:
            raise Exception("Invalid format. Expected space_NUMBER")
        else:
            return context_id
    raise Exception("Invalid format. Expected http://graasp.epfl.ch/#item=space_SOMETHING")
   

class PleNewSpacesPanel(L4lPleView):

    @expose(methods = ['GET', 'POST'])
    def index(self):
        form = SpaceUrlForm()
        if form.validate_on_submit():
            try:
                context_id = parse_space_url(form.url.data)
            except Exception as e:
                form.url.errors.append(e.message)
            else:
                create_new_space(context_id)
                return redirect(url_for('ple_admin_courses.index_view'))
        return self.render("ple_admin/new_space.html", form = form)

class PlePermissionToSpacePanel(L4lPleModelView):

    form_args = dict(
        permission_to_lms = dict(query_factory = lambda : PlePermissionToSpacePanel.permission_to_lms_filter()),
        course = dict(query_factory = lambda : PlePermissionToSpacePanel.course_filter()),
    )

    column_labels = dict(
        permission_to_lms = 'Permission',
        course = 'Space',
    )


    def __init__(self, session, **kwargs):
        super(PlePermissionToSpacePanel, self).__init__(PermissionToCourse, session, **kwargs)
        PlePermissionToSpacePanel.permission_to_lms_filter = create_permission_to_lms_filter(self.session)
        PlePermissionToSpacePanel.course_filter = create_course_filter(self.session)

    def get_query(self, *args, **kwargs):
        query_obj = super(PlePermissionToSpacePanel, self).get_query(*args, **kwargs)
        query_obj = query_obj.join(Course).filter_by(lms = current_user.lms)
        return query_obj

    def get_count_query(self, *args, **kwargs):
        query_obj = super(PlePermissionToSpacePanel, self).get_count_query(*args, **kwargs)
        query_obj = query_obj.join(Course).filter_by(lms = current_user.lms)
        return query_obj

############################################## 
# 
#    Initialization
# 
def init_ple_admin(app, db_session):
    ple_admin_url = '/ple_admin'
    ple_admin = Admin(index_view = PleAdminPanel(url=ple_admin_url, endpoint = 'ple_admin'), name = u"PLE admin", url = ple_admin_url, endpoint = 'ple-admin')
    ple_admin.add_view(PleInstructorLaboratoriesPanel( db_session, name = u"Labs", endpoint = 'ple_admin_labs', url = 'labs'))

    ple_admin.add_view(PleNewSpacesPanel(db_session,    category = u"Spaces", name     = u"New", endpoint = 'ple_admin_new_courses', url = 'spaces/create'))
    ple_admin.add_view(PleSpacesPanel(db_session,    category = u"Spaces", name     = u"Spaces", endpoint = 'ple_admin_courses', url = 'spaces'))
    ple_admin.add_view(PlePermissionToSpacePanel(db_session,    category = u"Spaces", name     = u"Permissions", endpoint = 'ple_admin_course_permissions', url = 'spaces/permissions'))

    ple_admin.add_view(PleUsersPanel(db_session,      name     = u"Users", endpoint = 'ple_admin_users', url = 'users'))
    ple_admin.add_view(RedirectView('logout',         name = u"Log out", endpoint = 'ple_admin_logout', url = 'logout'))
    ple_admin.init_app(app)

