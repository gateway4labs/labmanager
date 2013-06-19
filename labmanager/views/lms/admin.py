# -*-*- encoding: utf-8 -*-*-
#
# lms4labs is free software: you can redistribute it and/or modify
# it under the terms of the BSD 2-Clause License
# lms4labs is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.


import hashlib
import uuid
import traceback

from yaml import load as yload

from wtforms.fields import PasswordField

from flask import request, redirect, url_for, session

from flask.ext import wtf
from flask.ext.admin import Admin, AdminIndexView, BaseView, expose
from flask.ext.admin.contrib.sqlamodel import ModelView
from flask.ext.login import current_user

from labmanager.models import LmsUser, Course, Laboratory, PermissionToLms, PermissionToLmsUser, PermissionToCourse
from labmanager.views import RedirectView, retrieve_courses

config = yload(open('labmanager/config/config.yml'))

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

    column_list = ('login', 'full_name', 'access_level')

    form_columns = ('login', 'full_name', 'access_level', 'password')

    sel_choices = [(level, level.title()) for level in config['user_access_level']]

    form_overrides = dict(password=PasswordField, access_level=wtf.SelectField)
    form_args = dict( access_level=dict( choices=sel_choices ) )

    def __init__(self, session, **kwargs):
        super(LmsUsersPanel, self).__init__(LmsUser, session, **kwargs)

    def get_query(self, *args, **kwargs):
        query_obj = super(LmsUsersPanel, self).get_query(*args, **kwargs)
        query_obj = query_obj.filter_by(lms = current_user.lms)
        return query_obj

    def get_count_query(self, *args, **kwargs):
        query_obj = super(LmsUsersPanel, self).get_count_query(*args, **kwargs)
        query_obj = query_obj.filter_by(lms = current_user.lms)
        return query_obj

        

    def on_model_change(self, form, model):
        # TODO: don't update password always
        model.lms   = current_user.lms
        model.password = hashlib.new('sha',model.password).hexdigest()


def create_lms_user_filter(session):
    def filter():
        return session.query(LmsUser).filter_by(lms = current_user.lms)

    return staticmethod(filter)

def create_permission_to_lms_filter(session):
    def filter():
        return session.query(PermissionToLms).filter_by(lms = current_user.lms)

    return staticmethod(filter)


class PermissionToLmsUserPanel(L4lLmsModelView):

    can_edit = False

    lms_user_filter          = None
    permission_to_lms_filter = None

    form_args = dict(
        lms_user          = dict(query_factory = lambda : PermissionToLmsUserPanel.lms_user_filter()),
        permission_to_lms = dict(query_factory = lambda : PermissionToLmsUserPanel.permission_to_lms_filter()),
    )

    form_columns = ('lms_user', 'permission_to_lms')

    def __init__(self, session, **kwargs):
        super(PermissionToLmsUserPanel, self).__init__(PermissionToLmsUser, session, **kwargs)
        PermissionToLmsUserPanel.lms_user_filter = create_lms_user_filter(self.session)
        PermissionToLmsUserPanel.permission_to_lms_filter = create_permission_to_lms_filter(self.session)

    def get_query(self, *args, **kwargs):
        query_obj = super(PermissionToLmsUserPanel, self).get_query(*args, **kwargs)
        query_obj = query_obj.join(LmsUser).filter_by(lms = current_user.lms)
        return query_obj

    def get_count_query(self, *args, **kwargs):
        query_obj = super(PermissionToLmsUserPanel, self).get_count_query(*args, **kwargs)
        query_obj = query_obj.join(LmsUser).filter_by(lms = current_user.lms)
        return query_obj

    def on_model_change(self, form, model):

        existing_permission = self.session.query(PermissionToLmsUser).filter_by(lms_user = model.lms_user, permission_to_lms = model.permission_to_lms).first()

        if existing_permission:
            raise Exception("Existing permission on that user for that laboratory")

        key = u'%s_%s_%s' % (current_user.lms, model.lms_user.login, model.permission_to_lms.local_identifier)
        key = key.lower().replace(' ','_')
        final_key = u''
        for c in key:
            if c in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_-':
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

class LmsInstructorLaboratoriesPanel(L4lLmsModelView):

    can_delete = False
    can_edit   = False
    can_create = False

    def __init__(self, session, **kwargs):
        super(LmsInstructorLaboratoriesPanel, self).__init__(Laboratory, session, **kwargs)

    def get_query(self, *args, **kwargs):
        query_obj = super(LmsInstructorLaboratoriesPanel, self).get_query(*args, **kwargs)
        query_obj = query_obj.join(PermissionToLms).filter_by(lms = current_user.lms)
        return query_obj

    def get_count_query(self, *args, **kwargs):
        query_obj = super(LmsInstructorLaboratoriesPanel, self).get_count_query(*args, **kwargs)
        query_obj = query_obj.join(PermissionToLms).filter_by(lms = current_user.lms)
        return query_obj


#################################################
# 
#   Course management
# 

class LmsCoursesPanel(L4lLmsModelView):

    column_list = ('name', 'context_id')

    form_columns = ('name', 'context_id')

    def __init__(self, session, **kwargs):
        super(LmsCoursesPanel, self).__init__(Course, session, **kwargs)

    def get_query(self, *args, **kwargs):
        query_obj = super(LmsCoursesPanel, self).get_query(*args, **kwargs)
        query_obj = query_obj.filter_by(lms = current_user.lms)
        return query_obj

    def get_count_query(self, *args, **kwargs):
        query_obj = super(LmsCoursesPanel, self).get_count_query(*args, **kwargs)
        query_obj = query_obj.filter_by(lms = current_user.lms)
        return query_obj

class LmsCourseDiscoveryPanel(L4lLmsView):

    @expose(methods=["POST", "GET"])
    def index(self):
        basic_http_authentications = current_user.lms.basic_http_authentications
        if not basic_http_authentications:
            message = "No authentication is configured in your LMS. If you are not using the Basic HTTP system (e.g., you're using LTI), don't worry. Otherwise, contact the Labmanager administrator."
            return self.render("lms_admin/discover-errors.html", message = message)

        basic_http_authentication = basic_http_authentications[0]

        q     = request.args.get('q','')
        try:
            start = int(request.args.get('start','0'))
        except:
            start = 0

        user     = basic_http_authentication.labmanager_login
        password = basic_http_authentication.labmanager_password
        url = "%s?q=%s&start=%s" % (basic_http_authentication.lms_url, q, start)

        VISIBLE_PAGES = 10
        results = retrieve_courses(url, user, password)
        if isinstance(results, basestring):
            message = "Invalid JSON provided or could not connect to the LMS. Look at the logs for more information"
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
            message = "Malformed data retrieved. Look at the logs for more information"
            return self.render('lms_admin/discover-errors.html', message = message)

        if request.method == 'POST':
            courses_to_manage = []
            for key in request.form:
                if key.startswith('course-'):
                    courses_to_manage.append(key[len('course-'):])

            existing_courses = self.session.query(Course).filter(Course.context_id.in_(courses_to_manage), Course.lms == current_user.lms).all()
            existing_course_ids = [ existing_course.context_id for existing_course in existing_courses ]

            if request.form['action'] == 'add':
                for course_to_manage in courses_to_manage:
                    print course_to_manage not in existing_course_ids and course_to_manage in course_dict
                    if course_to_manage not in existing_course_ids and course_to_manage in course_dict:
                        new_course = Course(name = course_dict[course_to_manage], lms = current_user.lms, context_id = course_to_manage)
                        self.session.add(new_course)
            elif request.form['action'] == 'delete':
                for course_to_manage in courses_to_manage:
                    if course_to_manage in existing_course_ids:
                        existing_course = self.session.query(Course).filter(Course.context_id == course_to_manage, Course.lms == current_user.lms).first()
                        if existing_course:
                            self.session.delete(existing_course)
                        
            else:
                return self.render('lms_admin/discover-errors.html', message = "Invalid action found (add or delete expected)")

            self.session.commit()



        existing_courses = self.session.query(Course).filter(Course.context_id.in_(course_dict.keys()), Course.lms == current_user.lms).all()
        existing_course_ids = [ existing_course.context_id for existing_course in existing_courses ]

        return self.render("lms_admin/discover.html", current_page = current_page, current_pages = current_pages, max_page = max_page, q = q, start = start, courses = courses, per_page = per_page, max_position = number - VISIBLE_PAGES, max_position_page = (number - VISIBLE_PAGES) / VISIBLE_PAGES, existing_course_ids = existing_course_ids )

class LmsPermissionToCoursesPanel(L4lLmsModelView):

    form_args = dict(
        permission_to_lms = dict(query_factory = lambda : LmsPermissionToCoursesPanel.permission_to_lms_filter()),
    )


    def __init__(self, session, **kwargs):
        super(LmsPermissionToCoursesPanel, self).__init__(PermissionToCourse, session, **kwargs)
        LmsPermissionToCoursesPanel.permission_to_lms_filter = create_permission_to_lms_filter(self.session)

    def get_query(self, *args, **kwargs):
        query_obj = super(LmsPermissionToCoursesPanel, self).get_query(*args, **kwargs)
        query_obj = query_obj.join(Course).filter_by(lms = current_user.lms)
        return query_obj

    def get_count_query(self, *args, **kwargs):
        query_obj = super(LmsPermissionToCoursesPanel, self).get_count_query(*args, **kwargs)
        query_obj = query_obj.join(Course).filter_by(lms = current_user.lms)
        return query_obj

############################################## 
# 
#    Initialization
# 
def init_lms_admin(app, db_session):
    lms_admin_url = '/lms_admin'
    lms_admin = Admin(index_view = LmsAdminPanel(url=lms_admin_url, endpoint = 'lms_admin'), name = u"LMS admin", url = lms_admin_url, endpoint = 'lms-admin')
    lms_admin.add_view(LmsInstructorLaboratoriesPanel( db_session, name = u"Labs", endpoint = 'lms_admin_labs', url = 'labs'))
    lms_admin.add_view(LmsCoursesPanel(db_session,    category = u"Courses", name     = u"Courses", endpoint = 'lms_admin_courses', url = 'courses'))
    lms_admin.add_view(LmsCourseDiscoveryPanel(db_session,    category = u"Courses", name     = u"Discover", endpoint = 'lms_admin_course_discover', url = 'courses/discover'))
    lms_admin.add_view(LmsPermissionToCoursesPanel(db_session,    category = u"Courses", name     = u"Permissions", endpoint = 'lms_admin_course_permissions', url = 'courses/permissions'))
    lms_admin.add_view(LmsUsersPanel(db_session,      category = u"Users", name     = u"Users", endpoint = 'lms_admin_users', url = 'users'))
    lms_admin.add_view(PermissionToLmsUserPanel(db_session,      category = u"Users", name     = u"Permissions", endpoint = 'lms_admin_user_permissions', url = 'user_permissions'))
    lms_admin.add_view(RedirectView('logout',         name = u"Log out", endpoint = 'lms_admin_logout', url = 'logout'))
    lms_admin.init_app(app)

