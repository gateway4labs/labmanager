# -*-*- encoding: utf-8 -*-*-
# 
# lms4labs is free software: you can redistribute it and/or modify
# it under the terms of the BSD 2-Clause License
# lms4labs is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

from flask.ext.wtf import Form, TextField, Required, PasswordField, ValidationError

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
    name      = TextField("Name", validators = [ Required() ])
    url       = TextField("URL",  validators = [ Required() ])

    lms_login    = TextField("LMS login", validators = [ Required() ])
    lms_password = PasswordField("LMS password")

    labmanager_login    = TextField("Labmanager login", validators = [ Required() ])
    labmanager_password = PasswordField("Labmanager password")

    def __init__(self, add_or_edit, *args, **kwargs):
        super(AddLmsForm, self).__init__(*args, **kwargs)
        self.add_or_edit = add_or_edit

    def validate_lms_password(form, field):
        if form.add_or_edit and field.data == '':
            raise ValidationError("This field is required.")

    def validate_labmanager_password(form, field):
        if form.add_or_edit and field.data == '':
            raise ValidationError("This field is required.")

class AddUserForm(RetrospectiveForm):
    name      = TextField("Name", validators = [ Required() ])

    login     = TextField("Login", validators = [ Required() ])
    password  = PasswordField("Password")

    def __init__(self, add_or_edit, *args, **kwargs):
        super(AddUserForm, self).__init__(*args, **kwargs)
        self.add_or_edit = add_or_edit

    def validate_password(form, field):
        if form.add_or_edit and field.data == '':
            raise ValidationError("This field is required.")

class GenericPermissionForm(RetrospectiveForm):
    identifier    = TextField("Identifier", validators = [ Required() ])

