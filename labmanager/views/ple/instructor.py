# -*-*- encoding: utf-8 -*-*-
#
# gateway4labs is free software: you can redistribute it and/or modify
# it under the terms of the BSD 2-Clause License
# gateway4labs is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

#
# Copied from lms\instructor.py and modified in order to create ple\instructor.py
# Modified by ILZ #28
#

from flask import request, redirect, url_for, session, Markup

from flask.ext.admin import Admin, AdminIndexView, expose
from flask.ext.admin.contrib.sqlamodel import ModelView
from flask.ext.login import current_user

from labmanager.views import RedirectView
from labmanager.views.ple.admin import PlePermissionToSpacePanel, PleNewSpacesPanel, PleSpacesPanel
from labmanager.models import LMS,Laboratory, PermissionToLms
from labmanager.rlms import get_manager_class
# Added by ILZ issue 34
from flask.ext.babel import gettext, ngettext, lazy_gettext
# End

#################################################################
# 
#            Base class
# 

class PleAuthManagerMixin(object):
    def is_accessible(self):
        if not current_user.is_authenticated():
            return False

        return session['usertype'] == 'lms' and current_user.access_level == 'instructor'
    
class L4lPleInstructorModelView(PleAuthManagerMixin, ModelView):

    def _handle_view(self, name, **kwargs):
        if not self.is_accessible():
            return redirect(url_for('login_lms', next=request.url))

        return super(L4lPleInstructorModelView, self)._handle_view(name, **kwargs)

class L4lPleInstructorIndexView(PleAuthManagerMixin, AdminIndexView):

    def _handle_view(self, name, **kwargs):
        if not self.is_accessible():
            return redirect(url_for('login_lms', next=request.url))

        return super(L4lPleInstructorIndexView, self)._handle_view(name, **kwargs)

###############################################################
#
#              Index
# 

class PleInstructorPanel(L4lPleInstructorIndexView):
    @expose()
    def index(self):
        return self.render("ple_admin/instructors.html")
    
###############################################################
#
#              Permissions for this user
#

from labmanager.models import PermissionToLmsUser

class PermissionToPleUserPanel(L4lPleInstructorModelView):

    can_create = can_edit = can_delete = False

    def __init__(self, session, **kwargs):
        super(PermissionToPleUserPanel, self).__init__(PermissionToLmsUser, session, **kwargs)

    def get_query(self, *args, **kwargs):
        query_obj = super(PermissionToPleUserPanel, self).get_query(*args, **kwargs)
        query_obj = query_obj.filter_by(lms_user = current_user)
        return query_obj

    def get_count_query(self, *args, **kwargs):
        query_obj = super(PermissionToPleUserPanel, self).get_count_query(*args, **kwargs)
        query_obj = query_obj.filter_by(lms_user = current_user)
        return query_obj

###############################################
# 
#   Laboratories
# 

def local_id_formatter(v, c, laboratory, p):
    for permission in laboratory.lab_permissions:
        if permission.lms == current_user.lms:
            return permission.local_identifier
    return gettext('N/A')

def list_widgets_formatter(v, c, laboratory, p):
    return Markup('<a href="%s"> gettext("list") </a>' % url_for('.list_widgets', local_identifier = local_id_formatter(v, c, laboratory, p)))



def accessibility_formatter(v, c, lab, p):
    
    mylms = current_user.lms
    permissions = db_session.query(PermissionToLms).filter_by(lms = mylms, local_identifier = lab.default_local_identifier, accessible = True).first()

    # labaccessible shows what we want the lab to be (e.g. if it is currently  not accesible, then we want it accessible)
    if permissions is None:
        currently = gettext('This lab is NOT accesible')
        labaccessible = gettext('true')
        klass = 'btn-success'
        msg = gettext('Make accessible')

    else:
        currently = gettext('This lab IS accesible')
        labaccessible = gettext('false')
        klass = 'btn-danger'
        msg = gettext('Make not accessible')

                                       
    return Markup("""<form method='POST' action='%(url)s' style="text-align: center">
                        %(currently)s  
                        <input type='hidden' name='accessible_value' value='%(accessible_value)s'/>
                        <input type='hidden' name='lab_id' value='%(lab_id)s'/>
                        <input class='btn %(klass)s' type='submit' value="%(msg)s"></input>
                    </form>""" % dict(
                        url                      = url_for('.change_accessibility'),                     
                        accessible_value         = labaccessible,
                        lab_id                   = lab.id,      
                        klass                    = klass,
                        msg                      = msg,
                        currently                = currently,
                    ))



class PleInstructorLaboratoriesPanel(L4lPleInstructorModelView):

    can_delete = False
    can_edit   = False
    can_create = False

    column_list = ('rlms', 'name', 'laboratory_id', 'local_identifier', 'widgets')
    column_formatters = dict( local_identifier = local_id_formatter, widgets = list_widgets_formatter )
    column_labels = dict(rlms = lazy_gettext('RLMS'),
                                    name = lazy_gettext('Name'),
                                    laboratory_id = lazy_gettext('Laboratory Id'),
                                    local_identifier = lazy_gettext('Local Identifier'),
                                    widgets = lazy_gettext('widgets')) 

    def __init__(self, session, **kwargs):
        super(PleInstructorLaboratoriesPanel, self).__init__(Laboratory, session, **kwargs)

    def get_query(self, *args, **kwargs):
#        print current_user
#        print dir(current_user)
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
            return self.render("ple_admin/errors.html", message = gettext("Laboratory not found"))

        rlms_db = laboratory.rlms
        RLMS_CLASS = get_manager_class(rlms_db.kind, rlms_db.version)
        rlms = RLMS_CLASS(rlms_db.configuration)

        widgets = rlms.list_widgets(laboratory.laboratory_id)
        return self.render("ple_admin/list_widgets.html", widgets = widgets, institution_id = current_user.lms.name, lab_name = local_identifier)

#################################################
# 
#   Course management
# 

class PleInstructorNewSpacesPanel(PleAuthManagerMixin, PleNewSpacesPanel):
    """PleNewSpacesPanel, but accessible by instructors through PleAuthManagerMixin"""

class PleInstructorSpacesPanel(PleAuthManagerMixin, PleSpacesPanel):
    """PleSpacesPanel, but accessible by instructors through PleAuthManagerMixin""" 

class PleInstructorPermissionToSpacesPanel(PleAuthManagerMixin, PlePermissionToSpacePanel):
    """PlePermissionToSpacePanel but accessible by instructors through PleAuthManagerMixin"""
 
####################################################################
# 
#              Initialization
#

def init_ple_instructor_admin(app, db_session):
    ple_instructor_url = '/ple_instructor'
    ple_instructor = Admin(index_view = PleInstructorPanel(url=ple_instructor_url, endpoint = 'ple_instructor'), name = lazy_gettext(u'PLEinstructor'), url = ple_instructor_url, endpoint = 'ple_instructor')
    ple_instructor.add_view(PleInstructorLaboratoriesPanel(db_session, name = lazy_gettext(u'Laboratories'), endpoint = 'ple_instructor_laboratories', url = 'laboratories'))
    i18n_spaces=lazy_gettext(u'Spaces')
    ple_instructor.add_view(PleInstructorNewSpacesPanel(db_session,    category = i18n_spaces, name     = lazy_gettext(u'New'), endpoint = 'ple_instructor_new_courses', url = 'spaces/create'))
    ple_instructor.add_view(PleInstructorSpacesPanel(db_session,    category = i18n_spaces, name     = lazy_gettext(u'Spaces'), endpoint = 'ple_instructor_courses', url = 'spaces'))
    ple_instructor.add_view(PleInstructorPermissionToSpacesPanel(db_session,    category = i18n_spaces, name     = lazy_gettext(u'Permissions'), endpoint = 'ple_instructor_course_permissions', url = 'spaces/permissions'))

    ple_instructor.add_view(RedirectView('logout',         name = lazy_gettext(u'Log out'), endpoint = 'ple_instructor_logout', url = 'logout'))
    ple_instructor.init_app(app)