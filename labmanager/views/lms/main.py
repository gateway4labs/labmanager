from flask.ext.login import current_user
from flask.ext.admin import expose, AdminIndexView

class LmsPanel(AdminIndexView):
    def is_accessible(self):
        return current_user.is_authenticated()

