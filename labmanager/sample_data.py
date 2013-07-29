# -*-*- encoding: utf-8 -*-*-
#
# gateway4labs is free software: you can redistribute it and/or modify
# it under the terms of the BSD 2-Clause License
# gateway4labs is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

import json
import hashlib

from .db import db_session, init_db
from .models import LmsUser, PermissionToLms, Laboratory, PermissionToLmsUser
from .models import LMS, RLMS, PermissionToCourse, BasicHttpCredentials, ShindigCredentials, Course

def add_sample_users():

    init_db(drop = True)

    #################################################
    # 
    #     RLMS 1: WebLab-Deusto
    #   

    weblabdeusto_configuration = {
        'remote_login' : 'labmanager',
        'password'     : 'password',
        'base_url'     : 'http://www.weblab.deusto.es/weblab/',
    }

    rlms_weblabdeusto = RLMS(kind = u"WebLab-Deusto",
                       location = u"Bilbao, Spain",
                       url = u"https://www.weblab.deusto.es/",
                       version = u"5.0",
                       configuration = json.dumps(weblabdeusto_configuration) )
    db_session.add(rlms_weblabdeusto)

    robot_lab = Laboratory(name = u"robot-movement@Robot experiments",
                           laboratory_id = u"robot-movement@Robot experiments",
                           rlms = rlms_weblabdeusto)

    db_session.add(robot_lab)

    #######################################################
    # 
    #     RLMS 2: FCEIA UNR
    #   

    rlms_unr = RLMS(kind = u'FCEIA-UNR',
                       location = u'Rosario, Argentina',
                       url = u'http://labremf4a.fceia.unr.edu.ar/accesodeusto.aspx',
                       version = u"1.2.2",
                       configuration = json.dumps(dict(remote_login = 'login', password = 'password')))
    db_session.add(rlms_unr)

    physics_lab = Laboratory(name = u'unr-physics',
                           laboratory_id = u'unr-physics',
                           rlms = rlms_unr)

    db_session.add(physics_lab)


    #######################################################
    # 
    #     RLMS 3: iLabs (not implemented at this moment)
    #   


    rlms_ilab = RLMS(kind = u'iLabs',
                       location = u'MIT',
                       url = u'http://ilab.mit.edu/wiki/',
                       version = u"1.0",
                       configuration = json.dumps(dict(
                            sb_guid = 'ISB-247A4591CA1443485D85657CF357',
                            sb_url  = 'http://ludi.mit.edu/iLabServiceBroker/iLabServiceBroker.asmx',
                            authority_guid = 'fakeGUIDforRMLStest-12345',
                            group_name = 'Experiment_Group',
                       )))
    db_session.add(rlms_ilab)


    #######################################################
    #     
    #     LMS 1: Using LTI
    #    

    lms1 = LMS(full_name = u"Deusto Moodle (LTI)", name = "deusto",
                     url = u"http://alud2.deusto.es/")
    db_session.add(lms1)

    password = unicode(hashlib.new('sha', 'password').hexdigest())

    lms_admin      = LmsUser(login="admin", full_name="Administrator", lms = lms1, access_level = 'admin')
    lms_admin.password = password
    lms_instructor1 = LmsUser(login="instructor1", full_name="Instructor 1", lms = lms1, access_level = 'instructor')
    lms_instructor1.password = password
    lms_instructor2 = LmsUser(login="instructor2", full_name="Instructor 2", lms = lms1, access_level = 'instructor')
    lms_instructor2.password = password

    permission_to_lms1 = PermissionToLms(lms = lms1, laboratory = robot_lab, configuration = '', local_identifier = 'robot')
    db_session.add(permission_to_lms1)

    db_session.add(lms_admin)
    db_session.add(lms_instructor1)
    db_session.add(lms_instructor2)

    permission_instructor1 = PermissionToLmsUser(permission_to_lms = permission_to_lms1, lms_user = lms_instructor1, key = 'deusto_moodle_instructor1_robot', secret = 'abcdefghijklmnopqrstuvwxyz')

    permission_instructor2 = PermissionToLmsUser(permission_to_lms = permission_to_lms1, lms_user = lms_instructor2, key = 'deusto_moodle_instructor2_robot', secret = 'abcdefghijklmnopqrstuvwxyz')

    db_session.add(permission_instructor1)
    db_session.add(permission_instructor2)

    #######################################################
    #     
    #     LMS 2: Using LTI, too
    #    


    lms2 = LMS(full_name = u"Ilias Stuttgart (LTI)", name = "stuttgart",
                     url = u"https://ilias3.uni-stuttgart.de")
    db_session.add(lms2)

    lms_admin2   = LmsUser(login="admin", full_name="Administrator", lms = lms2, access_level = 'admin')
    lms_admin2.password = password
    lms_instructor1b = LmsUser(login="instructor1", full_name="Instructor 1 (at B)", lms = lms2, access_level = 'instructor')
    lms_instructor1b.password = password
    lms_instructor2b = LmsUser(login="instructor2", full_name="Instructor 2 (at B)", lms = lms2, access_level = 'instructor')
    lms_instructor2b.password = password

    db_session.add(lms_admin2)
    db_session.add(lms_instructor1b)
    db_session.add(lms_instructor2b)

    permission_to_lms2 = PermissionToLms(lms = lms2, laboratory = robot_lab, configuration = '', local_identifier = 'robot')
    db_session.add(permission_to_lms2)

    permission_instructor1b = PermissionToLmsUser(permission_to_lms = permission_to_lms2, lms_user = lms_instructor1b, key = 'ilias_stuttgart_instructor1_robot', secret = 'abcdefghijklmnopqrstuvwxyz')

    permission_instructor2b = PermissionToLmsUser(permission_to_lms = permission_to_lms2, lms_user = lms_instructor2b, key = 'ilias_stuttgart_instructor2_robot', secret = 'abcdefghijklmnopqrstuvwxyz')

    db_session.add(permission_instructor1b)
    db_session.add(permission_instructor2b)

    #######################################################
    #     
    #     LMS 3: Using Basic HTTP
    #    

    lms3 = LMS(full_name = u"UNED aLF (HTTP)", name = "uned",
                     url = u"https://www.innova.uned.es/")
    db_session.add(lms3)

    credential = BasicHttpCredentials(lms_login = 'uned', lms_password = password, lms = lms3, lms_url = 'http://localhost:5000/fake_list_courses/gateway4labs/list', labmanager_login = 'labmanager', labmanager_password = 'password')
    db_session.add(credential)

    lms_admin3   = LmsUser(login="admin", full_name="Administrator", lms = lms3, access_level = 'admin')
    lms_admin3.password = password

    db_session.add(lms_admin3)

    permission_to_lms3 = PermissionToLms(lms = lms3, laboratory = robot_lab, configuration = '', local_identifier = 'robot')
    db_session.add(permission_to_lms3)

    course1 = Course(name = "Physics course", lms = lms3, context_id = "physics")
    course2 = Course(name = "Robots course", lms = lms3, context_id = "robots")
    db_session.add(course1)
    db_session.add(course2)

    permission_to_course = PermissionToCourse(course = course2, permission_to_lms = permission_to_lms3)
    db_session.add(permission_to_course)

    #######################################################
    #     
    #     LMS 4: Using Shindig, school 1
    #    

    lms4 = LMS(full_name = u"School 1 at Graasp", name = "school1", url = u"http://graasp.epfl.ch/")
    db_session.add(lms4)

    credential = ShindigCredentials(lms = lms4, shindig_url = 'http://shindig.epfl.ch')
    db_session.add(credential)

    lms_admin4   = LmsUser(login="admin", full_name="Administrator", lms = lms4, access_level = 'admin')
    lms_admin4.password = password

    db_session.add(lms_admin4)

    permission_to_lms4 = PermissionToLms(lms = lms4, laboratory = robot_lab, configuration = '', local_identifier = 'robot')
    db_session.add(permission_to_lms4)

    course1 = Course(name = "Physics course", lms = lms4, context_id = "1234")
    course2 = Course(name = "Robots course", lms = lms4, context_id = "1235")
    db_session.add(course1)
    db_session.add(course2)

    permission_to_course = PermissionToCourse(course = course2, permission_to_lms = permission_to_lms4)
    db_session.add(permission_to_course)

    #######################################################
    #     
    #     LMS 5: Using Shindig, school 2
    #    

    lms5 = LMS(full_name = u"School 2 at Graasp", name = "school2", url = u"http://graasp.epfl.ch/")
    db_session.add(lms5)

    credential = ShindigCredentials(lms = lms5, shindig_url = 'http://shindig.epfl.ch')
    db_session.add(credential)

    lms_admin5  = LmsUser(login="admin", full_name="Administrator", lms = lms5, access_level = 'admin')
    lms_admin5.password = password

    db_session.add(lms_admin5)

    permission_to_lms5 = PermissionToLms(lms = lms5, laboratory = robot_lab, configuration = '', local_identifier = 'robot')
    db_session.add(permission_to_lms5)

    course1 = Course(name = "Other physics course", lms = lms5, context_id = "1236")
    course2 = Course(name = "Other robots course", lms = lms5, context_id = "1237")
    db_session.add(course1)
    db_session.add(course2)

    permission_to_course = PermissionToCourse(course = course2, permission_to_lms = permission_to_lms5)
    db_session.add(permission_to_course)

    db_session.commit()
