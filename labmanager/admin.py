from flask.ext.admin import Admin

from labmanager.models import LabManagerUser as User
from labmanager.models import NewLMS, Permission, Experiment, NewRLMS, Credential, NewCourse

from .views.admin.lms  import LMSPanel, CoursePanel
from .views.admin.rlms import RLMSPanel, ExperimentPanel, PermissionPanel
from .views.admin.main import AdminPanel, UsersPanel

def init_admin(app, db_session):
  """
  Creates a whole administration interface using Flask Admin.

  It will add a blueprint called `admin` to the `app` flask application.
  """

  admin = Admin(index_view = AdminPanel())

  admin.add_view(PermissionPanel(Permission, session=db_session))

  admin.add_view(LMSPanel(NewLMS,     session=db_session))
  admin.add_view(CoursePanel(NewCourse, session=db_session))

  admin.add_view(RLMSPanel(NewRLMS, session=db_session))
  admin.add_view(ExperimentPanel(Experiment, session=db_session))

  admin.add_view(UsersPanel(User, session=db_session))

  admin.init_app(app)
