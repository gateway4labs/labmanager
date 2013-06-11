from flask.ext.login import current_user

from labmanager.views.lms.admin import L4lLmsModelView
from labmanager.models import Course

class LmsCoursesPanel(L4lLmsModelView):

    column_list = ('name', 'context_id')

    form_columns = ('name', 'context_id')

    def __init__(self, session, **kwargs):
        super(LmsCoursesPanel, self).__init__(Course, session, **kwargs)

    def get_query(self, *args, **kwargs):
        query_obj = super(LmsCoursesPanel, self).get_query(*args, **kwargs)
        query_obj = query_obj.filter_by(lms = current_user.lms)
        return query_obj
        
