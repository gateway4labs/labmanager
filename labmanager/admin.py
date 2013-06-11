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

    from .views.admin import init_admin as init_admin
    init_admin(app, db_session)

    from .views.lms.admin import init_lms_admin
    init_lms_admin(app, db_session)

    from .views.lms.instructor import init_instructor_admin
    init_instructor_admin(app, db_session)
