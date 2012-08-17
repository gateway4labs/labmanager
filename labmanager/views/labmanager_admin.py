# -*-*- encoding: utf-8 -*-*-
# 
# lms4labs is free software: you can redistribute it and/or modify
# it under the terms of the BSD 2-Clause License
# lms4labs is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

"""
  :copyright: 2012 Pablo Orduña, Elio San Cristobal, Alberto Pesquera Martín
  :license: BSD, see LICENSE for more details
"""

#
# Python imports
import hashlib
import json
import traceback
from functools import wraps

# 
# Flask imports
# 
from flask import render_template, request, session, redirect, url_for, flash

# 
# LabManager imports
# 
from labmanager.database import db_session
from labmanager.models   import LMS, LabManagerUser, RLMSType, RLMSTypeVersion, RLMS, Laboratory, PermissionOnLaboratory
from labmanager.rlms     import get_supported_types, get_supported_versions, is_supported, get_form_class, get_manager_class, get_lms_permissions_form_class
from labmanager.forms    import AddLmsForm, AddUserForm

from labmanager import app
from labmanager.views import deletes_elements
from labmanager.views.lms_admin import _login_as_lms


###############################################################################
# 
# 
# 
#    I N T E R A C T I O N     W I T H     L A B M A N A G E R   A D M I N  
# 
# 
# 

def hash_password(password):
    return hashlib.new("sha", password).hexdigest()

def requires_labmanager_admin_session(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        logged_in    = session.get('logged_in', False)
        session_type = session.get('session_type', '')
        if not logged_in or session_type != 'labmanager_admin':
            return redirect(url_for('admin_login', next = request.url))
        return f(*args, **kwargs)
    return decorated

##############
# 
# L O G I N 
# 

@app.route("/lms4labs/labmanager/admin/login", methods = ['GET', 'POST'])
def admin_login():
    login_error = False

    if request.method == 'POST':
        login    = request.form['username']
        password = request.form['password']

        user = db_session.query(LabManagerUser).filter_by(login = login, password = hash_password(password) ).first()

        if user is not None:
            session['logged_in']    = True
            session['session_type'] = 'labmanager_admin'
            session['user_id']      = user.id
            session['user_name']    = user.name
            session['login']        = login

            next = request.args.get('next')
            if next is not None and next.startswith(app.config.get('URL_ROOT', request.url_root)) and next != '':
                return redirect(next)
            return redirect(url_for('admin_index'))

        login_error = True

    return render_template("labmanager_admin/login.html", login_error = login_error, next = request.args.get('next','') )

@app.route("/lms4labs/labmanager/admin/logout", methods = ['GET', 'POST'])
def admin_logout():
    session.pop('logged_in', None)
    return redirect(url_for('admin_login'))

@app.route("/lms4labs/labmanager/admin/logout/show", methods = ['GET', 'POST'])
def admin_before_logout():
    return render_template("labmanager_admin/logout.html")

############
# 
# H O M E
# 


@app.route("/lms4labs/labmanager/admin/")
@requires_labmanager_admin_session
def admin_index():
    return render_template("labmanager_admin/index.html")

############
# 
# L M S 
# 

@app.route("/lms4labs/labmanager/admin/lms/", methods = ['GET', 'POST'])
@requires_labmanager_admin_session
@deletes_elements(LMS)
def admin_lms():
    if request.method == 'POST' and request.form.get('action','').lower().startswith('add'):
        return redirect(url_for('admin_lms_add'))

    lmss = db_session.query(LMS).all()
    return render_template("labmanager_admin/lms.html", lmss = lmss)

def _add_or_edit_lms(id):
    form = AddLmsForm(id is None)

    if form.validate_on_submit():
        if id is None:
            new_lms = LMS(name = form.name.data, url = form.url.data, 
                            lms_login           = form.lms_login.data, 
                            lms_password        = hash_password(form.lms_password.data), 
                            labmanager_login    = form.labmanager_login.data, 
                            labmanager_password = form.labmanager_password.data)
            db_session.add(new_lms)
        else:
            lms = db_session.query(LMS).filter_by(id = id).first()
            if lms is None:
                return render_template("labmanager_admin/lms_errors.html")


            lms.url               = form.url.data
            lms.name              = form.name.data
            lms.lms_login         = form.lms_login.data
            lms.labmanager_login  = form.labmanager_login.data
            if form.lms_password.data:
                lms.lms_password        = hash_password(form.lms_password.data)
            if form.labmanager_password.data:
                lms.labmanager_password = form.labmanager_password.data

        db_session.commit()
        return redirect(url_for('admin_lms'))
    
    if id is not None:
        lms = db_session.query(LMS).filter_by(id = id).first()
        if lms is None:
            return render_template("labmanager_admin/lms_errors.html")

        name = lms.name

        form.url.data              = lms.url
        form.name.data             = lms.name
        form.lms_login.data        = lms.lms_login
        form.labmanager_login.data = lms.labmanager_login
    else:
        name = None

    return render_template("labmanager_admin/lms_add.html", form = form, name = name)

@app.route("/lms4labs/labmanager/admin/lms/<lms_login>/edit/", methods = ['GET', 'POST'])
@requires_labmanager_admin_session
def admin_lms_edit(lms_login):
    lms = db_session.query(LMS).filter_by(lms_login = lms_login).first()
    if lms is None:
        return render_template("labmanager_admin/lms_errors.html")

    return _add_or_edit_lms(lms.id)

@app.route("/lms4labs/labmanager/admin/lms/add/", methods = ['GET', 'POST'])
@requires_labmanager_admin_session
def admin_lms_add():
    return _add_or_edit_lms(id = None)

@app.route("/lms4labs/labmanager/admin/lms/<lms_login>/login/", methods = ['GET', 'POST'])
@requires_labmanager_admin_session
def admin_lms_login(lms_login):
    return _login_as_lms(session['user_name'], lms_login)

############
# 
# R L M S 
# 

@app.route("/lms4labs/labmanager/admin/rlms/", methods = ('GET','POST'))
@requires_labmanager_admin_session
@deletes_elements(RLMSType)
def admin_rlms():
    types = db_session.query(RLMSType).all()
    retrieved_types = set( (retrieved_type.name for retrieved_type in types) )

    if request.method == 'POST' and request.form.get('action','').lower().startswith('add'):
        for supported_type in get_supported_types():
            if supported_type not in retrieved_types:
                new_type = RLMSType(supported_type)
                db_session.add(new_type)
        db_session.commit()    
        types = db_session.query(RLMSType).all()
        retrieved_types = set( (retrieved_type.name for retrieved_type in types) )

    any_supported_missing = any([ supported_type not in retrieved_types for supported_type in get_supported_types()])

    return render_template("labmanager_admin/rlms_types.html", types = types, supported = get_supported_types(), any_supported_missing = any_supported_missing)

@app.route("/lms4labs/labmanager/admin/rlms/<rlmstype>/", methods = ('GET','POST'))
@requires_labmanager_admin_session
@deletes_elements(RLMSTypeVersion)
def admin_rlms_versions(rlmstype):
    rlms_type = db_session.query(RLMSType).filter_by(name = rlmstype).first()
    if rlms_type is not None:
        versions = rlms_type.versions

        retrieved_versions = set( (retrieved_version.version for retrieved_version in versions) )

        if request.method == 'POST' and request.form.get('action','').lower().startswith('add'):
            for supported_version in get_supported_versions(rlmstype):
                if supported_version not in retrieved_versions:
                    new_version = RLMSTypeVersion(rlms_type, supported_version)
                    db_session.add(new_version)
            db_session.commit()

            versions = rlms_type.versions
            retrieved_versions = set( (retrieved_version.version for retrieved_version in versions) )

        any_supported_missing = any([ supported_version not in retrieved_versions for supported_version in get_supported_versions(rlmstype)])

        return render_template("labmanager_admin/rlms_versions.html", versions = versions, name = rlms_type.name, supported = get_supported_versions(rlmstype), any_supported_missing = any_supported_missing )

    return render_template("labmanager_admin/rlms_errors.html")

def _get_rlms_version(rlmstype, rlmsversion):
    rlms_type = db_session.query(RLMSType).filter_by(name = rlmstype).first()
    if rlms_type is not None:
        rlms_version = ([ version for version in rlms_type.versions if version.version == rlmsversion ] or [None])[0]
        if rlms_version is not None:
            return rlms_version
    return None

def _add_or_edit_rlms(rlmstype, rlmsversion, id):
    if not is_supported(rlmstype, rlmsversion):
        return "Not supported"

    rlms_version = _get_rlms_version(rlmstype, rlmsversion)
    if rlms_version is None:
        return render_template("labmanager_admin/rlms_errors.html")

    if id is not None:
        rlms = db_session.query(RLMS).filter_by(id = id).first()
        if rlms is None or rlms.rlms_version != rlms_version:
            return render_template("labmanager_admin/rlms_errors.html")


    AddForm = get_form_class(rlmstype, rlmsversion)
    form = AddForm(id is None)

    if form.validate_on_submit():
        configuration_dict = {}
        for field in form.get_field_names():
            if field not in ('location', 'name'):
                configuration_dict[field] = getattr(form, field).data

        configuration = json.dumps(configuration_dict)
        
        if id is None:
            new_rlms = RLMS(name = form.name.data, location = form.location.data, rlms_version = rlms_version, configuration = configuration)
            db_session.add(new_rlms)
        else:
            rlms = db_session.query(RLMS).filter_by(id = id).first()
            if rlms is None:
                return render_template("labmanager_admin/rlms_errors.html")
            rlms.name          = form.name.data
            rlms.location      = form.location.data
            rlms.configuration = AddForm.process_configuration(rlms.configuration, configuration)

        db_session.commit()
        return redirect(url_for('admin_rlms_rlms', rlmstype = rlmstype, rlmsversion = rlmsversion))

    if id is not None:
        rlms = db_session.query(RLMS).filter_by(id = id).first()
        if rlms is None:
            return render_template("labmanager_admin/rlms_errors.html")

        form.name.data     = rlms.name
        form.location.data = rlms.location
        if rlms.configuration is not None and rlms.configuration != '':
            configuration = json.loads(rlms.configuration)
            for key in configuration:
                getattr(form, key).data = configuration[key]

    return render_template("labmanager_admin/rlms_rlms_add.html", rlmss = rlms_version.rlms, name = rlms_version.rlms_type.name, version = rlms_version.version, form = form)


@app.route("/lms4labs/labmanager/admin/rlms/<rlmstype>/<rlmsversion>/", methods = ('GET','POST'))
@requires_labmanager_admin_session
@deletes_elements(RLMS)
def admin_rlms_rlms(rlmstype, rlmsversion):
    if request.method == 'POST' and request.form.get('action','').lower().startswith('add'):
        return redirect(url_for('admin_rlms_rlms_add', rlmstype = rlmstype, rlmsversion=rlmsversion))

    rlms_version = _get_rlms_version(rlmstype, rlmsversion)
    if rlms_version is None:
        return render_template("labmanager_admin/rlms_errors.html")

    return render_template("labmanager_admin/rlms_rlms.html", rlmss = rlms_version.rlms, name = rlms_version.rlms_type.name, version = rlms_version.version)


@app.route("/lms4labs/labmanager/admin/rlms/<rlmstype>/<rlmsversion>/add/", methods = ('GET','POST'))
@requires_labmanager_admin_session
def admin_rlms_rlms_add(rlmstype, rlmsversion):
    return _add_or_edit_rlms(rlmstype, rlmsversion, None)

@app.route("/lms4labs/labmanager/admin/rlms/<rlmstype>/<rlmsversion>/<int:id>/", methods = ('GET','POST'))
@requires_labmanager_admin_session
def admin_rlms_rlms_edit(rlmstype, rlmsversion, id):
    return _add_or_edit_rlms(rlmstype, rlmsversion, id)

@app.route("/lms4labs/labmanager/admin/rlms/<rlmstype>/<rlmsversion>/<int:id>/labs/", methods = ('GET','POST'))
@requires_labmanager_admin_session
@deletes_elements(Laboratory)
def admin_rlms_rlms_list(rlmstype, rlmsversion, id):
    rlms = db_session.query(RLMS).filter_by(id = id).first()
    if rlms is None or rlms.rlms_version.version != rlmsversion or rlms.rlms_version.rlms_type.name != rlmstype:
        return render_template("labmanager_admin/rlms_errors.html")

    if request.method == 'POST':
        if request.form.get('action','') == 'add':
            return redirect(url_for('admin_rlms_rlms_list_external', rlmstype = rlmstype, rlmsversion = rlmsversion, id = id))

    laboratories = rlms.laboratories

    ManagerClass          = get_manager_class(rlmstype, rlmsversion)
    manager_class         = ManagerClass(rlms.configuration)
    try:
        confirmed_laboratories = manager_class.get_laboratories()
    except:
        traceback.print_exc()
        flash("There was an error retrieving laboratories. Check the trace")
        return render_template("labmanager_admin/rlms_errors.html")

    confirmed_laboratory_ids = [ confirmed_laboratory.laboratory_id for confirmed_laboratory in confirmed_laboratories ]

    return render_template("labmanager_admin/rlms_rlms_list.html", laboratories = laboratories, type_name = rlmstype, version = rlmsversion, rlms_name = rlms.name, confirmed_laboratory_ids = confirmed_laboratory_ids, rlms_id = rlms.id)

@app.route("/lms4labs/labmanager/admin/rlms/<rlmstype>/<rlmsversion>/<int:id>/externals/", methods = ('GET','POST'))
@requires_labmanager_admin_session
def admin_rlms_rlms_list_external(rlmstype, rlmsversion, id):
    rlms = db_session.query(RLMS).filter_by(id = id).first()
    if rlms is None or rlms.rlms_version.version != rlmsversion or rlms.rlms_version.rlms_type.name != rlmstype:
        return render_template("labmanager_admin/rlms_errors.html")

    existing_laboratory_ids = [ laboratory.laboratory_id for laboratory in rlms.laboratories ]

    ManagerClass          = get_manager_class(rlmstype, rlmsversion)
    manager_class         = ManagerClass(rlms.configuration)
    try:
        available_laboratories = manager_class.get_laboratories()
    except:
        traceback.print_exc()
        flash("There was an error retrieving laboratories. Check the trace")
        return render_template("labmanager_admin/rlms_errors.html")

    available_laboratory_ids = [ lab.laboratory_id for lab in available_laboratories ]

    if request.method == 'POST':
        if request.form.get('action','') == 'add':
            for laboratory_id in request.form:
                if laboratory_id != 'action' and laboratory_id in available_laboratory_ids and laboratory_id not in existing_laboratory_ids:
                    new_lab = Laboratory(laboratory_id, laboratory_id, rlms)
                    db_session.add(new_lab)
            db_session.commit()
            return redirect(url_for('admin_rlms_rlms_list', rlmstype = rlmstype, rlmsversion = rlmsversion, id = id))

    return render_template("labmanager_admin/rlms_rlms_list_external.html", available_laboratories = available_laboratories, type_name = rlmstype, version = rlmsversion, rlms_name = rlms.name, existing_laboratory_ids = existing_laboratory_ids)

def get_lab_and_lms(rlmstype, rlmsversion, id, lab_id):
    lab  = db_session.query(Laboratory).filter_by(id = lab_id).first()
    if lab is None:
        return None, None

    rlms = lab.rlms
    if rlms is None or rlms.id != id or rlms.rlms_version.version != rlmsversion or rlms.rlms_version.rlms_type.name != rlmstype:
        return None, None
    return lab, rlms


@app.route("/lms4labs/labmanager/admin/rlms/<rlmstype>/<rlmsversion>/<int:id>/labs/<int:lab_id>/permissions/", methods = ('GET','POST'))
@requires_labmanager_admin_session
@deletes_elements(Laboratory)
def admin_rlms_rlms_lab_edit_permissions(rlmstype, rlmsversion, id, lab_id):
    template_variables = {}

    lab, rlms = get_lab_and_lms(rlmstype, rlmsversion, id, lab_id)
    if lab is None or rlms is None:
        return render_template("labmanager_admin/rlms_errors.html")

    if request.method == 'POST':
        if request.form.get('action','').startswith('revoke-'):
            lms_login = request.form['action'][len('revoke-'):]
            lms = db_session.query(LMS).filter_by(lms_login = lms_login).first()
            if lms is None:
                return render_template("labmanager_admin/rlms_errors.html")
           
            permission = db_session.query(PermissionOnLaboratory).filter_by(laboratory_id = lab_id, lms_id = lms.id).first()
            if permission is not None:
                db_session.delete(permission)
                db_session.commit()

    granted_lms_ids = [ perm.lms_id for perm in lab.permissions ]

    lmss = db_session.query(LMS).all()

    template_variables['granted_lms_ids'] = granted_lms_ids
    template_variables['type_name']       = rlmstype
    template_variables['version']         = rlmsversion
    template_variables['rlms_name']       = rlms.name
    template_variables['rlms_id']         = id
    template_variables['lab_name']        = lab.name
    template_variables['lab_id']          = lab_id
    template_variables['lmss']            = lmss

    return render_template("labmanager_admin/rlms_rlms_lab_edit_permissions.html", **template_variables)

@app.route("/lms4labs/labmanager/admin/rlms/<rlmstype>/<rlmsversion>/<int:id>/labs/<int:lab_id>/permissions/<lms_login>", methods = ('GET','POST'))
@requires_labmanager_admin_session
@deletes_elements(Laboratory)
def admin_rlms_rlms_lab_edit_permissions_lms(rlmstype, rlmsversion, id, lab_id, lms_login):
    template_variables = {}

    lab, rlms = get_lab_and_lms(rlmstype, rlmsversion, id, lab_id)
    if lab is None or rlms is None:
        return render_template("labmanager_admin/rlms_errors.html")

    lms = db_session.query(LMS).filter_by(lms_login = lms_login).first()
    if lms is None:
        return render_template("labmanager_admin/rlms_errors.html")

    permission = db_session.query(PermissionOnLaboratory).filter_by(laboratory_id = lab_id, lms_id = lms.id).first()

    LmsPermissionsForm = get_lms_permissions_form_class(rlmstype, rlmsversion)
    form = LmsPermissionsForm()
    if form.validate_on_submit():
        configuration_dict = {}
        for field in form.get_field_names():
            if field != 'identifier':
                data = getattr(form, field).data
                if data != '':
                    configuration_dict[field] = data
        identifier = form.identifier.data

        configuration = json.dumps(configuration_dict)

        permission_with_same_identifier = db_session.query(PermissionOnLaboratory).filter_by(lms_id = lms.id, local_identifier = identifier).first()
        if permission_with_same_identifier is not None and permission_with_same_identifier != permission:
            flash("Could not grant permission. The identifier %s was already used in the LMS %s for the laboratory %s. Choose other identifier." % (identifier, lms.name, permission_with_same_identifier.laboratory.name))
            return render_template("labmanager_admin/rlms_errors.html")

        

        if permission is None: # Not yet granted: add it
            permission = PermissionOnLaboratory(lms = lms, laboratory = lab, configuration = configuration, local_identifier = identifier)
            db_session.add(permission)
        else: # Already granted: edit it
            permission.configuration = configuration

        db_session.commit()
        return redirect(url_for('admin_rlms_rlms_lab_edit_permissions', rlmstype = rlmstype, rlmsversion = rlmsversion, id = id, lab_id = lab_id))

    if permission is not None:
        configuration_dict = json.loads(permission.configuration or '{}')
        for field in configuration_dict:
            if hasattr(form, field):
                getattr(form, field).data = configuration_dict.get(field,'')
        form.identifier.data = permission.local_identifier

    template_variables['type_name']       = rlmstype
    template_variables['version']         = rlmsversion
    template_variables['rlms_name']       = rlms.name
    template_variables['rlms_id']         = id
    template_variables['lab_name']        = lab.name
    template_variables['lab_id']          = lab_id
    template_variables['lms_name']        = lms.name
    template_variables['add_or_edit']     = permission is None
    template_variables['form']            = form

    return render_template("labmanager_admin/rlms_rlms_lab_edit_permissions_add.html", **template_variables)

######################## 
# 
# U S E R S
# 
# 


@app.route("/lms4labs/labmanager/admin/user/", methods = ['GET', 'POST'])
@requires_labmanager_admin_session
@deletes_elements(LabManagerUser)
def admin_users():
    if request.method == 'POST' and request.form.get('action','').lower().startswith('add'):
        return redirect(url_for('admin_user_add'))

    users = db_session.query(LabManagerUser).all()
    return render_template("labmanager_admin/user.html", users = users)

def _add_or_edit_user(id):
    form = AddUserForm(id is None)

    if form.validate_on_submit():
        if id is None:
            new_user = LabManagerUser(login = form.login.data, name = form.name.data, 
                                    password = hash_password(form.password.data))
            db_session.add(new_user)
        else:
            user = db_session.query(LabManagerUser).filter_by(id = id).first()
            if user is None:
                return render_template("labmanager_admin/user_errors.html")


            user.name  = form.name.data
            user.login = form.login.data
            if form.password.data:
                user.password = hash_password(form.password.data)

        db_session.commit()
        return redirect(url_for('admin_users'))
    
    if id is not None:
        user = db_session.query(LabManagerUser).filter_by(id = id).first()
        if user is None:
            return render_template("labmanager_admin/user_errors.html")

        name = user.name

        form.name.data  = user.name
        form.login.data = user.login
    else:
        name = None

    return render_template("labmanager_admin/user_add.html", form = form, name = name)


@app.route("/lms4labs/labmanager/admin/user/add/", methods = ['GET', 'POST'])
@requires_labmanager_admin_session
def admin_user_add():
    return _add_or_edit_user(id = None)

@app.route("/lms4labs/labmanager/admin/user/<user_login>/edit/", methods = ['GET', 'POST'])
@requires_labmanager_admin_session
def admin_user_edit(user_login):
    user = db_session.query(LabManagerUser).filter_by(login = user_login).first()
    if user is None:
        return render_template("labmanager_admin/user_errors.html")

    return _add_or_edit_user(user.id)

