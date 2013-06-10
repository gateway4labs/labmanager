from flask import redirect, request, url_for

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

    from .views.lms.admin.main import LmsPanel
    from .views.lms.admin.user import LmsUsersPanel
    from .views.lms.admin.courses import LmsCoursesPanel

    lms_url = '/lms_admin'
    lms = Admin(index_view = LmsPanel(url=lms_url, endpoint = 'lms'), name = u"Lab Manager", url = lms_url, endpoint = lms_url)
    lms.add_view(LmsCoursesPanel(db_session,    name     = u"Courses", endpoint = 'mylms/courses'))
    lms.add_view(LmsUsersPanel(db_session,      name     = u"Users", endpoint = 'mylms/users'))
    lms.add_view(RedirectView('logout',         name = u"Log out", endpoint = 'mylms/logout'))
    lms.init_app(app)
