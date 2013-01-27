# -*-*- encoding: utf-8 -*-*-
import json
import urlparse

from yaml import load as yload

from flask import request, abort, Markup, url_for, Response
from flask.ext import wtf
from flask.ext.admin import expose

from labmanager.views.admin import L4lModelView, L4lBaseView

from labmanager.scorm import get_scorm_object
from labmanager.models import Permission, RLMS, Laboratory, PermissionOnLaboratory
from labmanager.rlms import get_form_class, get_supported_types, get_supported_versions, get_manager_class

config = yload(open('labmanager/config.yaml'))

class DynamicSelectWidget(wtf.widgets.Select):
    def __call__(self, *args, **kwargs):
        html = super(DynamicSelectWidget, self).__call__(*args, **kwargs)
        html = html.replace('<select ', '''<select onchange="document.location.replace(new String(document.location).replace(/&rlms=[^&]*/,'') + '&rlms=' + this.value)"''')
        return html

class DynamicSelectField(wtf.SelectField):
    widget = DynamicSelectWidget()


def _generate_choices():
    sel_choices = [('','')]
    for ins_rlms in get_supported_types():
        for ver in get_supported_versions(ins_rlms):
            sel_choices.append(("%s<>%s" % (ins_rlms, ver),"%s - %s" % (ins_rlms.title(), ver)) )
    return sel_choices

class RLMSPanel(L4lModelView):

    # For editing
    form_columns = ('kind', 'location', 'url')
    form_overrides = dict(kind=DynamicSelectField)

    # For listing 
    column_list  = ['kind', 'version', 'location', 'url', 'labs']
    column_exclude_list = ('version','configuration')

    column_formatters = dict(
            labs = lambda c, rlms, p: Markup('<a href="%s">List</a>' % (url_for('.labs', id=rlms.id)))
        )

    def __init__(self, session, **kwargs):
        super(RLMSPanel, self).__init__(RLMS, session, **kwargs)
        
        # 
        # For each supported RLMS, it provides a different edition
        # form. So as to avoid creating a new class each type for 
        # the particular form required, we must create a cache of
        # form classes.
        #
        self.__create_form_classes = {}
   
    def _get_cached_form_class(self, rlms, form):
        if rlms in self.__create_form_classes:
            form_class = self.__create_form_classes[rlms]
        else:
            # If it does not exist, we find the RLMS creation form
            rlmstype, rlmsversion = rlms.split('<>')
            rlms_form_class = get_form_class(rlmstype, rlmsversion)
            
            # And we create and register a new class for it
            class form_class(rlms_form_class, form.__class__):
                pass
            self.__create_form_classes[rlms] = form_class
        return form_class

    def _fill_form_instance(self, form, old_form, obj):
        form.csrf_token.data = old_form.csrf_token.data
        form.process(obj=obj)
        form.csrf_token.data = old_form.csrf_token.data

        for key in form.get_field_names():
            if key in request.form:
                getattr(form, key).data = request.form[key]

    def create_form(self, obj = None, *args, **kwargs):
        form = super(RLMSPanel, self).create_form(*args, **kwargs)
        rlms = request.args.get('rlms')

        if rlms is not None and '<>' in rlms:
            form_class = self._get_cached_form_class(rlms, form)

            old_form = form
            form = form_class(add_or_edit=True, fields=form._fields)
            form.kind.default = rlms
            self._fill_form_instance(form, old_form, obj)
        form.kind.choices = _generate_choices()
        return form

    def edit_form(self, obj, *args, **kwargs):
        form = super(RLMSPanel, self).edit_form(*args, **kwargs)
        form_class = self._get_cached_form_class(obj.kind + u'<>' + obj.version , form)
        old_form = form
        form = form_class(add_or_edit=False, fields=form._fields)
        del form.kind
        
        configuration = json.loads(obj.configuration)
        for key in configuration:
            # TODO: this should be RLMS specific
            if 'password' not in key: 
                setattr(obj, key, configuration[key])

        self._fill_form_instance(form, old_form, obj )
        return form

    def on_model_change(self, form, model):
        if model.kind == '':
            abort(406)
        
        if '<>' in model.kind:
            rlms_ver = model.kind.split('<>')
            model.kind, model.version = rlms_ver[0], rlms_ver[1]

        if not model.configuration:
            other_data = {}
        else:
            other_data = json.loads(model.configuration)

        for key in form.get_field_names():
            if key not in RLMSPanel.form_columns:
                # TODO: this should be RLMS specific
                if 'password' in key and getattr(form, key).data == '':
                    pass # Passwords can be skipped
                else:
                    other_data[key] = getattr(form, key).data
        
        model.configuration = json.dumps(other_data)

    @expose('/labs/<id>/', methods = ['GET','POST'])
    def labs(self, id):
        # 
        # TODO: CSRF is not used here. Security hole
        # 

        rlms_db = self.session.query(RLMS).filter_by(id = id).first()
        if rlms_db is None:
            return abort(404)

        RLMS_CLASS = get_manager_class(rlms_db.kind, rlms_db.version)
        rlms = RLMS_CLASS(rlms_db.configuration)
        labs = rlms.get_laboratories()

        registered_labs = [ lab.laboratory_id for lab in rlms_db.laboratories ]

        if request.method == 'POST':
            selected = []
            for name, value in request.form.items():
                if name != 'action' and value == 'on':
                    for lab in labs:
                        if lab.laboratory_id == name:
                            selected.append(lab)
            changes = False

            if request.form['action'] == 'register':
                for lab in selected:
                    if not lab.laboratory_id in registered_labs:
                        self.session.add(Laboratory(name = lab.name, laboratory_id = lab.laboratory_id, rlms = rlms_db))
                        changes = True

            elif request.form['action'] == 'unregister':

                for lab in selected:
                    if lab.laboratory_id in registered_labs:
                        cur_lab_db = None
                        for lab_db in rlms_db.laboratories:
                            if lab_db.laboratory_id == lab.laboratory_id:
                                cur_lab_db = lab_db
                                break

                        if cur_lab_db is not None:
                            self.session.delete(cur_lab_db)
                            changes = True

            if changes:
                self.session.commit()

        registered_labs = [ lab.laboratory_id for lab in rlms_db.laboratories ]

        return self.render('admin/lab-list.html', rlms = rlms_db, labs = labs, registered_labs = registered_labs)

class LaboratoryPanel(L4lModelView):

    can_create = False
    can_edit   = False

    def __init__(self, session, **kwargs):
        super(LaboratoryPanel, self).__init__(Laboratory, session, **kwargs)

def scorm_formatter(c, permission, p):
    
    for auth in permission.lms.authentications:
        if auth.kind == 'basic':
            return Markup('<a href="%s">Download</a>' % (url_for('.get_scorm', lms_id = permission.lms.id,  local_id = permission.local_identifier)))

    return 'N/A'

class PermissionOnLaboratoryPanel(L4lModelView):
    # 
    # TODO: manage configuration
    # 

    column_list = ('laboratory', 'lms', 'local_identifier', 'configuration', 'SCORM')

    column_descriptions = dict(
                laboratory       = u"Laboratory",
                lms              = u"Learning Management System",
                local_identifier = u"Unique identifier for a LMS to access a laboratory",
            )

    column_formatters = dict( SCORM = scorm_formatter )


    def __init__(self, session, **kwargs):
        super(PermissionOnLaboratoryPanel, self).__init__(PermissionOnLaboratory, session, **kwargs)

    @expose('/scorm/<lms_id>/scorm_<local_id>.zip')
    def get_scorm(self, lms_id, local_id):
        permission = self.session.query(PermissionOnLaboratory).filter_by(lms_id = lms_id, local_identifier = local_id).one()
        
        db_lms = permission.lms 

        lms_path = urlparse.urlparse(db_lms.url).path or '/'
        extension = '/'
        if 'lms4labs/' in lms_path:
            extension = lms_path[lms_path.rfind('lms4labs/lms/list') + len('lms4labs/lms/list'):]
            lms_path  = lms_path[:lms_path.rfind('lms4labs/')]

        contents = get_scorm_object(False, local_id, lms_path, extension)
        return Response(contents, headers = {'Content-Type' : 'application/zip', 'Content-Disposition' : 'attachment; filename=scorm_%s.zip' % local_id})
        

class PermissionPanel(L4lModelView):

#    form_columns = ('course', 'laboratory','configuration','access')
    sel_choices = [(status, status.title()) for status in config['permission_status']]
    form_overrides = dict(access=wtf.SelectField)
    form_args = dict(
            access=dict( choices=sel_choices )
        )

    def __init__(self, session, **kwargs):
        super(PermissionPanel, self).__init__(Permission, session, **kwargs)

