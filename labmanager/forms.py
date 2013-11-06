# -*-*- encoding: utf-8 -*-*-
# 
# gateway4labs is free software: you can redistribute it and/or modify
# it under the terms of the BSD 2-Clause License
# gateway4labs is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

from flask.ext.wtf import Form, TextField, Required, PasswordField, ValidationError
from labmanager.babel import gettext, ngettext, lazy_gettext

class RetrospectiveForm(Form):

    def get_field_names(self):
        field_names = []
        for field in self:
            if 'csrf' not in str(type(field)).lower():
                field_names.append(field.name)
        return field_names


class AddForm(RetrospectiveForm):
    pass

class AddLmsForm(RetrospectiveForm):
    name      = TextField(lazy_gettext("Name"), validators = [ Required() ])
    url       = TextField(lazy_gettext("URL"),  validators = [ Required() ])

    lms_login    = TextField(lazy_gettext("LMS login"), validators = [ Required() ])
    lms_password = PasswordField(lazy_gettext("LMS password"))

    labmanager_login    = TextField(lazy_gettext("Labmanager login"), validators = [ Required() ])
    labmanager_password = PasswordField(lazy_gettext("Labmanager password"))

    def __init__(self, add_or_edit, *args, **kwargs):
        super(AddLmsForm, self).__init__(*args, **kwargs)
        self.add_or_edit = add_or_edit

    def validate_lms_password(form, field):
        if form.add_or_edit and field.data == '':
            raise ValidationError(gettext("This field is required."))

    def validate_labmanager_password(form, field):
        if form.add_or_edit and field.data == '':
            raise ValidationError(gettext("This field is required."))

class AddUserForm(RetrospectiveForm):
    name      = TextField(lazy_gettext("Name"), validators = [ Required() ])

    login     = TextField(lazy_gettext("Login"), validators = [ Required() ])
    password  = PasswordField(lazy_gettext("Password"))

    def __init__(self, add_or_edit, *args, **kwargs):
        super(AddUserForm, self).__init__(*args, **kwargs)
        self.add_or_edit = add_or_edit

    def validate_password(form, field):
        if form.add_or_edit and field.data == '':
            raise ValidationError(gettext("This field is required."))

class GenericPermissionForm(RetrospectiveForm):
    identifier    = TextField(lazy_gettext("Identifier"), validators = [ Required() ])

