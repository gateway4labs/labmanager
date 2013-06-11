from flask import redirect, url_for

from flask.ext.admin import Admin, BaseView, expose

class RedirectView(BaseView):

    def __init__(self, redirection_url, *args, **kwargs):
        self.redirection_url = redirection_url
        super(RedirectView, self).__init__(*args, **kwargs)

    @expose()
    def index(self):
        return redirect(url_for(self.redirection_url))


def init_admin(app, db_session):
    """
    Creates a whole administration interface using Flask Admin.

    It will add a blueprint called `admin` to the `app` flask application.
    """

    from .views.admin.lms  import LMSPanel, CoursePanel
    from .views.admin.rlms import RLMSPanel, LaboratoryPanel, PermissionPanel, PermissionToLmsPanel
    from .views.admin.main import AdminPanel, UsersPanel, LmsUsersPanel

    admin_url = '/admin'

    admin = Admin(index_view = AdminPanel(url=admin_url), name = u"Lab Manager", url = admin_url, endpoint = admin_url)

    admin.add_view(PermissionPanel(db_session,             category = u"Permissions", name = u"Course permissions", endpoint = 'permissions/course'))
    admin.add_view(PermissionToLmsPanel(db_session, category = u"Permissions", name = u"LMS permissions",    endpoint = 'permissions/lms'))

    admin.add_view(LMSPanel(db_session,        category = u"LMS Management", name = u"LMS",     endpoint = 'lms/lms'))
    admin.add_view(CoursePanel(db_session,     category = u"LMS Management", name = u"Courses", endpoint = 'lms/courses'))

    admin.add_view(RLMSPanel(db_session,       category = u"ReLMS Management", name = u"RLMS",            endpoint = 'rlms/rlms'))
    admin.add_view(LaboratoryPanel(db_session, category = u"ReLMS Management", name = u"Registered labs", endpoint = 'rlms/labs'))

    admin.add_view(UsersPanel(db_session,      category = u"Users", name = u"Labmanager Users", endpoint = 'users/labmanager'))
    admin.add_view(LmsUsersPanel(db_session,   category = u"Users", name = u"LMS Users",        endpoint = 'users/lms'))

    admin.add_view(RedirectView('logout',      name = u"Log out", endpoint = 'admin/logout'))

    admin.init_app(app)

    from .views.lms.admin.main import LmsAdminPanel
    from .views.lms.admin.user import LmsUsersPanel
    from .views.lms.admin.courses import LmsCoursesPanel

    lms_admin_url = '/lms_admin'
    lms_admin = Admin(index_view = LmsAdminPanel(url=lms_admin_url, endpoint = 'lms-admin'), name = u"LMS admin", url = lms_admin_url, endpoint = lms_admin_url)
    lms_admin.add_view(LmsCoursesPanel(db_session,    name     = u"Courses", endpoint = 'mylms/courses'))
    lms_admin.add_view(LmsUsersPanel(db_session,      name     = u"Users", endpoint = 'mylms/users'))
    lms_admin.add_view(RedirectView('logout',         name = u"Log out", endpoint = 'mylms/logout'))
    lms_admin.init_app(app)

    from .views.lms.instructor.main import LmsInstructorPanel

    lms_instructor_url = '/lms_instructor'
    lms_instructor = Admin(index_view = LmsInstructorPanel(url=lms_instructor_url, endpoint = 'lms-instructor'), name = u"LMS instructor", url = lms_instructor_url, endpoint = lms_instructor_url)
    lms_instructor.add_view(RedirectView('logout',         name = u"Log out", endpoint = 'mycourses/logout'))
    lms_instructor.init_app(app)
