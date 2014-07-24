# -*-*- encoding: utf-8 -*-*-
#
# gateway4labs is free software: you can redistribute it and/or modify
# it under the terms of the BSD 2-Clause License
# gateway4labs is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

import uuid
import traceback
import urlparse

from hashlib import new as new_hash
from yaml import load as yload
from wtforms.fields import PasswordField
from flask import request, redirect, url_for, session, Markup, Response
from flask.ext import wtf
from flask.ext.admin import Admin, AdminIndexView, BaseView, expose
from flask.ext.admin.contrib.sqlamodel import ModelView
from flask.ext.login import current_user
from labmanager.babel import gettext, lazy_gettext
from labmanager.scorm import get_scorm_object
from labmanager.models import LtUser, Course, Laboratory, PermissionToLt, PermissionToLtUser, PermissionToCourse
from labmanager.views import RedirectView, retrieve_courses
import labmanager.forms as forms
from labmanager.utils import data_filename
from labmanager.db import db

config = yload(open(data_filename('labmanager/config/config.yml')))

#################################################################
# 
#            Base class
# 

class LmsAuthManagerMixin(object):
    def is_accessible(self):
        if not current_user.is_authenticated():
            return False
        return session['usertype'] == 'lms' and current_user.access_level == 'admin'
    
class L4lLmsModelView(LmsAuthManagerMixin, ModelView):
    def _handle_view(self, name, **kwargs):
        if not self.is_accessible():
            return redirect(url_for('login_lms', next=request.url))
        return super(L4lLmsModelView, self)._handle_view(name, **kwargs)

class L4lLmsAdminIndexView(LmsAuthManagerMixin, AdminIndexView):
    def _handle_view(self, name, **kwargs):
        if not self.is_accessible():
            return redirect(url_for('login_lms', next=request.url))
        return super(L4lLmsAdminIndexView, self)._handle_view(name, **kwargs)

class L4lLmsView(LmsAuthManagerMixin, BaseView):
    def __init__(self, session, **kwargs):
        self.session = session
        super(L4lLmsView, self).__init__(**kwargs)

    def _handle_view(self, name, **kwargs):
        if not self.is_accessible():
            return redirect(url_for('login_lms', next=request.url))
        return super(L4lLmsView, self)._handle_view(name, **kwargs)

##############################################
# 
#    Index
# 

class LmsAdminPanel(L4lLmsAdminIndexView):
    @expose()
    def index(self):
        return self.render("lms_admin/index.html")

###############################################
# 
#   User management
# 

class LmsUsersPanel(L4lLmsModelView):

    column_list = ['login', 'full_name', 'access_level']
    form_columns = ('login', 'full_name', 'access_level', 'password')
    column_labels = dict(login = lazy_gettext('Login'),
                                    full_name = lazy_gettext('Full Name'),
                                    access_level = lazy_gettext('Access Level'),
                                    password = lazy_gettext('Password'))  
    sel_choices = [(level, level.title()) for level in config['user_access_level']]
    form_overrides = dict(password=PasswordField, access_level=wtf.SelectField)
    form_args = dict( access_level=dict( choices=sel_choices ),
                            login=dict(validators=forms.USER_LOGIN_DEFAULT_VALIDATORS[:]),
                           password=dict(validators=forms.USER_PASSWORD_DEFAULT_VALIDATORS[:]))            
                           
    def __init__(self, session, **kwargs):
        super(LmsUsersPanel, self).__init__(LtUser, session, **kwargs)

    def get_query(self, *args, **kwargs):
        query_obj = super(LmsUsersPanel, self).get_query(*args, **kwargs)
        query_obj = query_obj.filter_by(lt = current_user.lt)
        return query_obj

    def get_count_query(self, *args, **kwargs):
        query_obj = super(LmsUsersPanel, self).get_count_query(*args, **kwargs)
        query_obj = query_obj.filter_by(lt = current_user.lt)
        return query_obj
        
    def create_model(self, form):
        if form.password.data == '':
            form.password.errors.append(lazy_gettext("This field is required."))
            return False
        form.password.data = unicode(new_hash("sha", form.password.data.encode('utf8')).hexdigest())
        return super(LmsUsersPanel, self).create_model(form)

    def on_model_change(self, form, model):
        model.lt = current_user.lt

    def update_model(self, form, model):
        old_password = model.password
        if form.password.data != '':
            form.password.data = unicode(new_hash("sha", form.password.data.encode('utf8')).hexdigest())
        return_value = super(LmsUsersPanel, self).update_model(form, model)
        if form.password.data == '':
            model.password = old_password
            self.session.add(model)
            self.session.commit()
        return return_value

def create_lms_user_filter(session):
    def filter():
        return session.query(LtUser).filter_by(lt = current_user.lt)
    return staticmethod(filter)

def create_permission_to_lms_filter(session):
    def filter():
        return session.query(PermissionToLt).filter_by(lt = current_user.lt)
    return staticmethod(filter)

def create_course_filter(session):
    def filter():
        return session.query(Course).filter_by(lt = current_user.lt)
    return staticmethod(filter)

class PermissionToLmsUserPanel(L4lLmsModelView):

    can_edit = False
    form_columns = ('lt_user', 'permission_to_lt')
    column_labels = dict(permission_to_lt = lazy_gettext('Permission To LT'),
                                    lms_user = lazy_gettext('LT User'),
                                    key = lazy_gettext('Key'),
                                    secret = lazy_gettext('Secret'))
    lt_user_filter          = None
    permission_to_lt_filter = None
    form_args = dict(
        lt_user          = dict(query_factory = lambda : PermissionToLmsUserPanel.lt_user_filter()),
        permission_to_lt = dict(query_factory = lambda : PermissionToLmsUserPanel.permission_to_lt_filter()),
    )
                                   
    def __init__(self, session, **kwargs):
        super(PermissionToLmsUserPanel, self).__init__(PermissionToLtUser, session, **kwargs)
        PermissionToLmsUserPanel.lt_user_filter = create_lms_user_filter(self.session)
        PermissionToLmsUserPanel.permission_to_lt_filter = create_permission_to_lms_filter(self.session)

    def get_query(self, *args, **kwargs):
        query_obj = super(PermissionToLmsUserPanel, self).get_query(*args, **kwargs)
        query_obj = query_obj.join(LtUser).filter_by(lt = current_user.lt)
        return query_obj

    def get_count_query(self, *args, **kwargs):
        query_obj = super(PermissionToLmsUserPanel, self).get_count_query(*args, **kwargs)
        query_obj = query_obj.join(LtUser).filter_by(lt = current_user.lt)
        return query_obj

    def on_model_change(self, form, model):
        existing_permission = self.session.query(PermissionToLtUser).filter_by(lt_user = model.lt_user, permission_to_lt = model.permission_to_lt).first()
        if existing_permission:
            raise Exception(gettext("Existing permission on that user for that laboratory"))
        key = u'%s_%s_%s' % (current_user.lt, model.lt_user.login, model.permission_to_lt.local_identifier)
        key = key.lower().replace(' ','_')
        final_key = u''
        for c in key:
            if c in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-':
                final_key += c
            else:
                final_key += '_'
        # uuid4 returns a random string (based on random functions, not in any characteristic of this computer or network)
        secret = uuid.uuid4().hex
        model.key    = final_key
        model.secret = secret

###############################################
# 
#   Laboratories
# 

def local_id_formatter(v, c, laboratory, p):
    for permission in laboratory.lab_permissions:
        if permission.lt == current_user.lt:
            return permission.local_identifier
    return gettext('N/A')

def scorm_formatter(v, c, laboratory, p):
    if current_user.lt.basic_http_authentications:
        for permission in laboratory.lab_permissions:
            if permission.lt == current_user.lt:
                local_id = permission.local_identifier
                return Markup('<a href="%s">Download</a>' % (url_for('.get_scorm', local_id = local_id)))
    return gettext('N/A')

class LmsInstructorLaboratoriesPanel(L4lLmsModelView):

    can_delete = False
    can_edit   = False
    can_create = False

    column_list = ['rlms', 'name', 'laboratory_id', 'local_identifier', 'SCORM']
    column_labels = dict(rlms = lazy_gettext('Rlms'),
                                    name = lazy_gettext('Name'),
                                    laboratory_id = lazy_gettext('Laboratory Id'),
                                    local_identifier = lazy_gettext('Local Identifier'),
                                    scorm =lazy_gettext('Scorm'))
    column_formatters = dict( SCORM = scorm_formatter, local_identifier = local_id_formatter )
                                    
    def __init__(self, session, **kwargs):
        super(LmsInstructorLaboratoriesPanel, self).__init__(Laboratory, session, **kwargs)

    def get_query(self, *args, **kwargs):
        query_obj = super(LmsInstructorLaboratoriesPanel, self).get_query(*args, **kwargs)
        query_obj = query_obj.join(PermissionToLt).filter_by(lt = current_user.lt)
        return query_obj

    def get_count_query(self, *args, **kwargs):
        query_obj = super(LmsInstructorLaboratoriesPanel, self).get_count_query(*args, **kwargs)
        query_obj = query_obj.join(PermissionToLt).filter_by(lt = current_user.lt)
        return query_obj

    @expose('/scorm/scorm_<local_id>.zip')
    def get_scorm(self, local_id):
        db_lt = current_user.lt
        if db_lt.basic_http_authentications:
            url = db_lt.basic_http_authentications[0].lt_url or ''
        else:
            url = ''
        lt_path = urlparse.urlparse(url).path or '/'
        extension = '/'
        if 'gateway4labs/' in lt_path:
            extension = lt_path[lt_path.rfind('gateway4labs/lms/list') + len('gateway4labs/lms/list'):]
            lt_path  = lt_path[:lt_path.rfind('gateway4labs/')]
        contents = get_scorm_object(False, local_id, lt_path, extension)
        return Response(contents, headers = {'Content-Type' : 'application/zip', 'Content-Disposition' : 'attachment; filename=scorm_%s.zip' % local_id})

#################################################
# 
#   Course management
# 

class LmsCoursesPanel(L4lLmsModelView):

    column_list = ['name', 'context_id']
    form_columns = ('name', 'context_id')
    column_labels = dict(name = lazy_gettext('Name'),
                                    context_id = lazy_gettext('Context Id'))

    def __init__(self, session, **kwargs):
        super(LmsCoursesPanel, self).__init__(Course, session, **kwargs)

    def get_query(self, *args, **kwargs):
        query_obj = super(LmsCoursesPanel, self).get_query(*args, **kwargs)
        query_obj = query_obj.filter_by(lt = current_user.lt)
        return query_obj

    def get_count_query(self, *args, **kwargs):
        query_obj = super(LmsCoursesPanel, self).get_count_query(*args, **kwargs)
        query_obj = query_obj.filter_by(lt = current_user.lt)
        return query_obj

    def on_model_change(self, form, model):
        model.lt   = current_user.lt

class LmsCourseDiscoveryPanel(L4lLmsView):
    @expose(methods=["POST", "GET"])
    def index(self):
        basic_http_authentications = current_user.lt.basic_http_authentications
        if not basic_http_authentications:
            message = gettext("No authentication is configured in your LMS. If you are not using the Basic HTTP system (e.g., you're using LTI), don't worry. Otherwise, contact the Labmanager administrator.")
            return self.render("lms_admin/discover-errors.html", message = message)
        basic_http_authentication = basic_http_authentications[0]
        q     = request.args.get('q','')
        try:
            start = int(request.args.get('start','0'))
        except:
            start = 0
        user     = basic_http_authentication.labmanager_login
        password = basic_http_authentication.labmanager_password
        url = "%s?q=%s&start=%s" % (basic_http_authentication.lt_url, q, start)
        VISIBLE_PAGES = 10
        results = retrieve_courses(url, user, password)
        if isinstance(results, basestring):
            message = gettext("Invalid JSON provided or could not connect to the LMS. Look at the logs for more information")
            return self.render("lms_admin/discover-errors.html", message = message)
        try:
            courses_data = results['courses']
            courses = [ (course['id'], course['name']) for course in courses_data ]
            course_dict = dict(courses)
            number   = int(results['number'])
            per_page = int(results['per-page'])
            number_of_pages = ((number - 1) / per_page ) + 1
            current_page    = ((start - 1)  / per_page ) + 1
            THEORICAL_BEFORE_PAGES = VISIBLE_PAGES / 2
            if current_page < THEORICAL_BEFORE_PAGES:
                BEFORE_PAGES = current_page
                AFTER_PAGES  = VISIBLE_PAGES - current_page
            else:
                BEFORE_PAGES = THEORICAL_BEFORE_PAGES
                AFTER_PAGES  = BEFORE_PAGES
            min_page = (start/VISIBLE_PAGES - BEFORE_PAGES)
            max_page = (start/VISIBLE_PAGES + AFTER_PAGES)
            if max_page >= number_of_pages:
                max_page = number_of_pages
            if min_page <= -1:
                min_page = 0
            current_pages   = range(min_page, max_page)
        except:
            traceback.print_exc()
            message = gettext("Malformed data retrieved. Look at the logs for more information")
            return self.render('lms_admin/discover-errors.html', message = message)
        if request.method == 'POST':
            courses_to_manage = []
            for key in request.form:
                if key.startswith('course-'):
                    courses_to_manage.append(key[len('course-'):])
            existing_courses = self.session.query(Course).filter(Course.context_id.in_(courses_to_manage), Course.lt == current_user.lt).all()
            existing_course_ids = [ existing_course.context_id for existing_course in existing_courses ]
            if request.form['action'] == 'add':
                for course_to_manage in courses_to_manage:
                    print course_to_manage not in existing_course_ids and course_to_manage in course_dict
                    if course_to_manage not in existing_course_ids and course_to_manage in course_dict:
                        new_course = Course(name = course_dict[course_to_manage], lt = current_user.lt, context_id = course_to_manage)
                        self.session.add(new_course)
            elif request.form['action'] == 'delete':
                for course_to_manage in courses_to_manage:
                    if course_to_manage in existing_course_ids:
                        existing_course = self.session.query(Course).filter(Course.context_id == course_to_manage, Course.lt == current_user.lt).first()
                        if existing_course:
                            self.session.delete(existing_course)
            else:
                return self.render('lms_admin/discover-errors.html', message = gettext("Invalid action found (add or delete expected)"))
            self.session.commit()
        existing_courses = self.session.query(Course).filter(Course.context_id.in_(course_dict.keys()), Course.lt == current_user.lt).all()
        existing_course_ids = [ existing_course.context_id for existing_course in existing_courses ]
        return self.render("lms_admin/discover.html", current_page = current_page, current_pages = current_pages, max_page = max_page, q = q, start = start, courses = courses, per_page = per_page, max_position = number - VISIBLE_PAGES, max_position_page = (number - VISIBLE_PAGES) / VISIBLE_PAGES, existing_course_ids = existing_course_ids )

class LmsPermissionToCoursesPanel(L4lLmsModelView):

    column_labels = dict(permission_to_lms = lazy_gettext('Permission To LT'),
                                    course = lazy_gettext('Course'),
                                    configuration = lazy_gettext('Configuration'))
    form_args = dict(
        permission_to_lms = dict(query_factory = lambda : LmsPermissionToCoursesPanel.permission_to_lms_filter()),
        course = dict(query_factory = lambda : LmsPermissionToCoursesPanel.course_filter()),
    )

    def __init__(self, session, **kwargs):
        super(LmsPermissionToCoursesPanel, self).__init__(PermissionToCourse, session, **kwargs)
        LmsPermissionToCoursesPanel.permission_to_lms_filter = create_permission_to_lms_filter(self.session)
        LmsPermissionToCoursesPanel.course_filter = create_course_filter(self.session)

    def get_query(self, *args, **kwargs):
        query_obj = super(LmsPermissionToCoursesPanel, self).get_query(*args, **kwargs)
        query_obj = query_obj.join(Course).filter_by(lt = current_user.lt)
        return query_obj

    def get_count_query(self, *args, **kwargs):
        query_obj = super(LmsPermissionToCoursesPanel, self).get_count_query(*args, **kwargs)
        query_obj = query_obj.join(Course).filter_by(lt = current_user.lt)
        return query_obj

############################################## 
# 
#    Initialization
# 
def init_lms_admin(app):
    lms_admin_url = '/lms_admin'
    lms_admin = Admin(index_view = LmsAdminPanel(url=lms_admin_url, endpoint = 'lms_admin'), name = lazy_gettext(u'LMS admin'), url = lms_admin_url, endpoint = 'lms-admin')
    lms_admin.add_view(LmsInstructorLaboratoriesPanel( db.session, name = lazy_gettext(u"Lab"), endpoint = 'lms_admin_labs', url = 'labs'))
    i18n_courses=lazy_gettext(u"Courses")
    lms_admin.add_view(LmsCoursesPanel(db.session,    category = i18n_courses, name     = lazy_gettext(u"Courses"), endpoint = 'lms_admin_courses', url = 'courses'))
    lms_admin.add_view(LmsCourseDiscoveryPanel(db.session,    category = i18n_courses, name     = lazy_gettext(u'Discover'), endpoint = 'lms_admin_course_discover', url = 'courses/discover'))
    lms_admin.add_view(LmsPermissionToCoursesPanel(db.session,    category =i18n_courses, name     = lazy_gettext(u'Permissions'), endpoint = 'lms_admin_course_permissions', url = 'courses/permissions'))
    i18n_users=lazy_gettext(u'Users')
    lms_admin.add_view(LmsUsersPanel(db.session,      category = i18n_users, name     = lazy_gettext(u'Users'), endpoint = 'lms_admin_users', url = 'users'))
    lms_admin.add_view(PermissionToLmsUserPanel(db.session,      category = i18n_users, name     = lazy_gettext(u'Permissions'), endpoint = 'lms_admin_user_permissions', url = 'user_permissions'))
    lms_admin.add_view(RedirectView('logout',         name = lazy_gettext(u'Log out'), endpoint = 'lms_admin_logout', url = 'logout'))
    lms_admin.init_app(app)
