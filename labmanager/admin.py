from flask.ext.admin import Admin

def init_admin(app, db_session):
    """
    Creates a whole administration interface using Flask Admin.

    It will add a blueprint called `admin` to the `app` flask application.
    """

    from .views.admin.lms  import LMSPanel, CoursePanel
    from .views.admin.rlms import RLMSPanel, LaboratoryPanel, PermissionPanel, PermissionOnLaboratoryPanel
    from .views.admin.main import AdminPanel, UsersPanel, LmsUsersPanel

    admin_url = '/admin'

    admin = Admin(index_view = AdminPanel(url=admin_url), name = u"Lab Manager", url = admin_url, endpoint = admin_url)

    admin.add_view(PermissionPanel(db_session,             category = u"Permissions", name = u"Course permissions", endpoint = 'permissions/course'))
    admin.add_view(PermissionOnLaboratoryPanel(db_session, category = u"Permissions", name = u"LMS permissions",    endpoint = 'permissions/lms'))

    admin.add_view(LMSPanel(db_session,        category = u"LMS Management", name = u"LMS",     endpoint = 'lms/lms'))
    admin.add_view(CoursePanel(db_session,     category = u"LMS Management", name = u"Courses", endpoint = 'lms/courses'))

    admin.add_view(RLMSPanel(db_session,       category = u"ReLMS Management", name = u"RLMS",            endpoint = 'rlms/rlms'))
    admin.add_view(LaboratoryPanel(db_session, category = u"ReLMS Management", name = u"Registered labs", endpoint = 'rlms/labs'))

    admin.add_view(UsersPanel(db_session,      category = u"Users", name = u"Labmanager Users", endpoint = 'users/labmanager'))
    admin.add_view(LmsUsersPanel(db_session,   category = u"Users", name = u"LMS Users",        endpoint = 'users/lms'))

    admin.init_app(app)

    from .views.lms.main import LmsPanel
    from .views.lms.user import LmsUsersPanel

    lms_url = '/lms'
    lms = Admin(index_view = LmsPanel(url=lms_url, endpoint = 'lms'), name = u"Lab Manager", url = lms_url, endpoint = lms_url)
    lms.add_view(LmsUsersPanel(db_session,      name     = u"Users", endpoint = 'lms/users'))
    lms.init_app(app)
