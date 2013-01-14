from flask.ext.admin import Admin

from .views.admin.lms  import LMSPanel, CoursePanel
from .views.admin.rlms import RLMSPanel, LaboratoryPanel, PermissionPanel
from .views.admin.main import AdminPanel, UsersPanel

def init_admin(app, db_session):
  """
  Creates a whole administration interface using Flask Admin.

  It will add a blueprint called `admin` to the `app` flask application.
  """

  admin = Admin(index_view = AdminPanel(url='/admin'), name = 'Lab Manager')

  admin.add_view(PermissionPanel(db_session))

  admin.add_view(LMSPanel(db_session))
  admin.add_view(CoursePanel(db_session))

  admin.add_view(RLMSPanel(db_session))
  admin.add_view(LaboratoryPanel(db_session))

  admin.add_view(UsersPanel(db_session))

  admin.init_app(app)
