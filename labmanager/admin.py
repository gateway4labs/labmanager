from flask.ext.admin import Admin

from .views.admin.lms  import LMSPanel, CoursePanel
from .views.admin.rlms import RLMSPanel, LaboratoryPanel, PermissionPanel, PermissionOnLaboratoryPanel
from .views.admin.main import AdminPanel, UsersPanel

def init_admin(app, db_session):
    """
    Creates a whole administration interface using Flask Admin.

    It will add a blueprint called `admin` to the `app` flask application.
    """

    admin_url = '/admin'

    admin = Admin(index_view = AdminPanel(url=admin_url), name = u"Lab Manager", url = admin_url, endpoint = admin_url)

    admin.add_view(PermissionPanel(db_session,             category = u"Permissions", name = u"Course permissions", endpoint = 'permissions/course'))
    admin.add_view(PermissionOnLaboratoryPanel(db_session, category = u"Permissions", name = u"LMS permissions",    endpoint = 'permissions/lms'))

    admin.add_view(LMSPanel(db_session,        category = u"LMS", name = u"LMS",     endpoint = 'lms/lms'))
    admin.add_view(CoursePanel(db_session,     category = u"LMS", name = u"Courses", endpoint = 'lms/courses'))

    admin.add_view(RLMSPanel(db_session,       category = u"ReLMS", name = u"RLMS",            endpoint = 'rlms/rlms'))
    admin.add_view(LaboratoryPanel(db_session, category = u"ReLMS", name = u"Registered labs", endpoint = 'rlms/labs'))

    admin.add_view(UsersPanel(db_session,      name     = u"Users", endpoint = 'users'))

    admin.init_app(app)

    lms_url = '/lms'
    # lms = Admin(index_view = AdminPanel(url=lms_url), name = u"Lab Manager", url = lms_url, endpoint = lms_url)
    lms = Admin(name = u"Lab Manager", url = lms_url, endpoint = lms_url)
    lms.init_app(app)
