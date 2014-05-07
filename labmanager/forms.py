# -*-*- encoding: utf-8 -*-*-
# 
# gateway4labs is free software: you can redistribute it and/or modify
# it under the terms of the BSD 2-Clause License
# gateway4labs is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

from flask.ext.wtf import Form, TextField, Required, PasswordField, ValidationError, validators
from labmanager.babel import gettext, lazy_gettext

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

# Basic model validators
# login can accept uppercases, lowercases, numbers, "_" and "." and must be at least 5 characters long
# password can accept any caracter except " " and must be at least 8 characters long
 
class GenericPermissionForm(RetrospectiveForm):
    identifier    = TextField(lazy_gettext("Identifier"), validators = [ Required() ])

def login_validator(form, field):
    invalid_chars = [ c
                            for c in field.data
                            if c.isupper() or not c.isalnum() and c not in '._' ]
    if invalid_chars:
        raise ValidationError(gettext('Invalid characters found: %(char)s', char=', '.join(invalid_chars)))
    if len(field.data) < 5:
        raise ValidationError(gettext('login lenght must be at least 5 characters long'))

USER_LOGIN_DEFAULT_VALIDATORS = [validators.Regexp("^[a-z0-9\.\_]{5,}$"), login_validator]

def password_validator(form, field):
    if len(field.data) > 0:
        invalid_chars = [ c
                                for c in field.data
                                if c.isspace() ]
    if invalid_chars:
        raise ValidationError(gettext('Passwords can not contain a space'))
    if len(field.data) < 8:
        raise ValidationError(gettext('password lenght must be at least 8 characters long'))

USER_PASSWORD_DEFAULT_VALIDATORS = [validators.Optional(),validators.Regexp("[^\s]{8,}"), password_validator]

# Registrarion Form validations
# login can accept uppercases, lowercases, numbers, "_" and "." and must be at least 5 characters long
# password can accept any caracter except " " and must be at least 8 characters long

class RegistrationPermissionForm(RetrospectiveForm):
    identifier    = TextField(lazy_gettext("Identifier"), validators = [ Required() ])

def school_full_name_validator(form, field):
    if len(field.data) < 4 or len(field.data) > 50:
        raise ValidationError(gettext('Oficial name must be between 4 and 50 characters long'))
        
SCHOOL_FULL_NAME_VALIDATORS = [school_full_name_validator]
        
def school_short_name_validator(form, field):
    if len(field.data) < 4 or len(field.data) > 15:
        raise ValidationError(gettext('Short name must be between 4 and 15 characters long'))
    else:
        invalid_chars = [ c
                                for c in field.data 
                                    if not c.isalnum() and c not in '.']
    if invalid_chars:
         raise ValidationError(gettext('Invalid characters found: %(char)s', char=', '.join(invalid_chars)))
        
SCHOOL_SHORT_NAME_VALIDATORS = [validators.Regexp("^[a-z0-9\.]{4,15}$"), school_short_name_validator]

def user_full_name_validator(form, field):
    if len(field.data) < 4 or len(field.data) > 15:
        raise ValidationError(gettext('Oficial name must be between 4 and 15 characters long'))

USER_FULL_NAME_VALIDATORS = [user_full_name_validator]
