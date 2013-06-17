# -*-*- encoding: utf-8 -*-*-
#
# lms4labs is free software: you can redistribute it and/or modify
# it under the terms of the BSD 2-Clause License
# lms4labs is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

import json
import hashlib

from .db import db_session, init_db

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

    lms1 = LMS(name = u"My Moodle",
                     url = u"http://moodle.com.co.co")
    db_session.add(lms1)

    password = unicode(hashlib.new('sha', 'password').hexdigest())

    lms_admin   = LmsUser(login="admin", full_name="Administrator", lms = lms1, access_level = 'admin')
    lms_admin.password = password
    lms_instructor1 = LmsUser(login="instructor1", full_name="Instructor 1", lms = lms1, access_level = 'instructor')
    lms_instructor1.password = password
    lms_instructor2 = LmsUser(login="instructor2", full_name="Instructor 2", lms = lms1, access_level = 'instructor')
    lms_instructor2.password = password

    db_session.add(lms_admin)
    db_session.add(lms_instructor1)
    db_session.add(lms_instructor2)

    course1 = Course(name = u"EE101",
                        lms = lms1,
                        context_id = u"1")
    db_session.add(course1)

    permission_to_lms1 = PermissionToLms(lms = lms1, laboratory = robot_lab, configuration = '', local_identifier = 'robot')

    permission1 = PermissionToCourse(context = course1,
                             permission_to_lms = permission_to_lms1,
                             access = u"pending")
    db_session.add(permission1)

    auth1 = LmsCredential(key = u"admin",
                      kind = u"OAuth1.0",
                      secret = u"80072568beb3b2102325eb203f6d0ff92f5cef8e",
                      lms = lms1)
    db_session.add(auth1)

    lms2 = LMS(name = u"My Moodle 2",
                     url = u"http://moodle.com.co.co")
    db_session.add(lms2)

    lms_admin2   = LmsUser(login="admin", full_name="Administrator", lms = lms2, access_level = 'admin')
    lms_admin2.password = password
    lms_instructor1b = LmsUser(login="instructor1b", full_name="Instructor 1 (at B)", lms = lms2, access_level = 'instructor')
    lms_instructor1b.password = password
    lms_instructor2b = LmsUser(login="instructor2b", full_name="Instructor 2 (at B)", lms = lms2, access_level = 'instructor')
    lms_instructor2b.password = password

    db_session.add(lms_admin2)
    db_session.add(lms_instructor1b)
    db_session.add(lms_instructor2b)

    course2 = Course(name = u"EE102",
                        lms = lms2,
                        context_id = u"1")
    db_session.add(course2)

    permission_to_lms2 = PermissionToLms(lms = lms2, laboratory = robot_lab, configuration = '', local_identifier = 'robot')

    permission2 = PermissionToCourse(context = course2,
                             permission_to_lms = permission_to_lms2,
                             access = u"pending")
    db_session.add(permission2)

    auth2 = LmsCredential(key = u"admin",
                      kind = u"OAuth1.0",
                      secret = u"80072568beb3b2102325eb203f6d0ff92f5cef8e",
                      lms = lms2)
    db_session.add(auth2)

    db_session.commit()
