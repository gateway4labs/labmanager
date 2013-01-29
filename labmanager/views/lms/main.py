from flask.ext.login import current_user
from flask.ext.admin import expose, AdminIndexView

class LmsPanel(AdminIndexView):
    def is_accessible(self):
        # TODO: is user authenticated
        # return current_user.is_authenticated()
        return True

