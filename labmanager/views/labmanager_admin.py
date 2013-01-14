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
from flask import render_template, request, session, redirect, url_for, flash, Blueprint

# 
# LabManager imports
# 
from labmanager.database import db_session
from labmanager.models   import LMS, LabManagerUser, RLMS, Laboratory, PermissionOnLaboratory
from labmanager.rlms     import get_supported_types, get_supported_versions, is_supported, get_form_class, get_manager_class, get_lms_permissions_form_class
from labmanager.forms    import AddLmsForm, AddUserForm

from labmanager.views import deletes_elements, get_authentication_scorm, retrieve_courses
from labmanager.views.lms_admin import _login_as_lms


labmanager = Blueprint('labmanager', __name__)

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

############
#
# L M S
#

@labmanager.route("/admin/lms_authenticate_<lms_login>.zip")
@requires_labmanager_admin_session
@deletes_elements(LMS)
def admin_lms_authenticate_scorm(lms_login):
    db_lms = db_session.query(LMS).filter_by(lms_login = lms_login).first()
    if db_lms is None:
        return render_template("labmanager_admin/lms_errors.html")

    return get_authentication_scorm(db_lms.url)

@labmanager.route("/admin/lms/<lms_login>/login/", methods = ['GET', 'POST'])
@requires_labmanager_admin_session
def admin_lms_login(lms_login):
    return _login_as_lms(session['user_name'], lms_login)


def get_lab_and_lms(rlmstype, rlmsversion, id, lab_id):
    lab  = db_session.query(Laboratory).filter_by(id = lab_id).first()
    if lab is None:
        return None, None

    rlms = lab.rlms
    if rlms is None or rlms.id != id or rlms.rlms_version.version != rlmsversion or rlms.rlms_version.rlms_type.name != rlmstype:
        return None, None
    return lab, rlms

