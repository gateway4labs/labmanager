# -*-*- encoding: utf-8 -*-*-
#
# lms4labs is free software: you can redistribute it and/or modify
# it under the terms of the BSD 2-Clause License
# lms4labs is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

import json
import hashlib

from .database import db_session, init_db

def add_sample_users():
    from labmanager.models import LmsUser, PermissionToLms, Laboratory
    from labmanager.models import LMS, RLMS, PermissionToCourse, LmsCredential, Course

    init_db(drop = True)

    configuration = {
        'remote_login' : 'weblabfed',
        'password'     : 'password',
        'base_url'     : 'http://www.weblab.deusto.es/weblab/',
    }

    rlms1 = RLMS(kind = u"WebLab-Deusto",
                       location = u"Deusto Spain",
                       url = u"https://www.weblab.deusto.es/",
                       version = u"5.0",
                       configuration = json.dumps(configuration) )
    db_session.add(rlms1)

    rlms2 = RLMS(kind = u'iLabs',
                       location = u'MIT',
                       url = u'http://ilab.mit.edu/wiki/',
                       version = u"1.2.2")
    db_session.add(rlms2)



    robot_lab = Laboratory(name = u"robot-movement@Robot experiments",
                           laboratory_id = u"robot-movement@Robot experiments",
                           rlms = rlms1)

    newlms1 = LMS(name = u"My Moodle",
                     url = u"http://moodle.com.co.co")
    db_session.add(newlms1)

    password = unicode(hashlib.new('sha', 'password').hexdigest())

    lms_admin   = LmsUser(login="admin", full_name="Administrator", lms = newlms1, access_level = 'admin')
    lms_admin.password = password
    lms_instructor1 = LmsUser(login="instructor1", full_name="Instructor 1", lms = newlms1, access_level = 'instructor')
    lms_instructor1.password = password
    lms_instructor2 = LmsUser(login="instructor2", full_name="Instructor 2", lms = newlms1, access_level = 'instructor')
    lms_instructor2.password = password

    db_session.add(lms_admin)
    db_session.add(lms_instructor1)
    db_session.add(lms_instructor2)

    course1 = Course(name = u"EE101",
                        lms = newlms1,
                        context_id = u"1")
    db_session.add(course1)

    permission_to_lms1 = PermissionToLms(lms = newlms1, laboratory = robot_lab, configuration = '', local_identifier = 'robot')

    permission1 = PermissionToCourse(context = course1,
                             permission_to_lms = permission_to_lms1,
                             access = u"pending")
    db_session.add(permission1)

    auth1 = LmsCredential(key = u"admin",
                      kind = u"OAuth1.0",
                      secret = u"80072568beb3b2102325eb203f6d0ff92f5cef8e",
                      lms = newlms1)
    db_session.add(auth1)

    db_session.commit()
