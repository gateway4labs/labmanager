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
from .models import LtUser, PermissionToLt, Laboratory, PermissionToLtUser
from .models import LearningTool, RLMS, PermissionToCourse, BasicHttpCredentials, ShindigCredentials, Course

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
    #     LT 1: Using LTI
    #    

    lt1 = LearningTool(full_name = u"Deusto Moodle (LTI)", name = "deusto",
                     url = u"http://alud2.deusto.es/")
    db_session.add(lt1)

    password = unicode(hashlib.new('sha', 'password').hexdigest())

    lt_admin      = LtUser(login="admin", full_name="Administrator", lt = lt1, access_level = 'admin')
    lt_admin.password = password
    lt_instructor1 = LtUser(login="instructor1", full_name="Instructor 1", lt = lt1, access_level = 'instructor')
    lt_instructor1.password = password
    lt_instructor2 = LtUser(login="instructor2", full_name="Instructor 2", lt = lt1, access_level = 'instructor')
    lt_instructor2.password = password

    permission_to_lt1 = PermissionToLt(lt = lt1, laboratory = robot_lab, configuration = '', local_identifier = 'robot')
    db_session.add(permission_to_lt1)

    db_session.add(lt_admin)
    db_session.add(lt_instructor1)
    db_session.add(lt_instructor2)

    permission_instructor1 = PermissionToLtUser(permission_to_lt = permission_to_lt1, lt_user = lt_instructor1, key = 'deusto_moodle_instructor1_robot', secret = 'abcdefghijklmnopqrstuvwxyz')

    permission_instructor2 = PermissionToLtUser(permission_to_lt = permission_to_lt1, lt_user = lt_instructor2, key = 'deusto_moodle_instructor2_robot', secret = 'abcdefghijklmnopqrstuvwxyz')

    db_session.add(permission_instructor1)
    db_session.add(permission_instructor2)

    #######################################################
    #     
    #     LT 2: Using LTI, too
    #    


    lt2 = LearningTool(full_name = u"Ilias Stuttgart (LTI)", name = "stuttgart",
                     url = u"https://ilias3.uni-stuttgart.de")
    db_session.add(lt2)

    lt_admin2   = LtUser(login="admin", full_name="Administrator", lt = lt2, access_level = 'admin')
    lt_admin2.password = password
    lt_instructor1b = LtUser(login="instructor1", full_name="Instructor 1 (at B)", lt = lt2, access_level = 'instructor')
    lt_instructor1b.password = password
    lt_instructor2b = LtUser(login="instructor2", full_name="Instructor 2 (at B)", lt = lt2, access_level = 'instructor')
    lt_instructor2b.password = password

    db_session.add(lt_admin2)
    db_session.add(lt_instructor1b)
    db_session.add(lt_instructor2b)

    permission_to_lt2 = PermissionToLt(lt = lt2, laboratory = robot_lab, configuration = '', local_identifier = 'robot')
    db_session.add(permission_to_lt2)

    permission_instructor1b = PermissionToLtUser(permission_to_lt = permission_to_lt2, lt_user = lt_instructor1b, key = 'ilias_stuttgart_instructor1_robot', secret = 'abcdefghijklmnopqrstuvwxyz')

    permission_instructor2b = PermissionToLtUser(permission_to_lt = permission_to_lt2, lt_user = lt_instructor2b, key = 'ilias_stuttgart_instructor2_robot', secret = 'abcdefghijklmnopqrstuvwxyz')

    db_session.add(permission_instructor1b)
    db_session.add(permission_instructor2b)

    #######################################################
    #     
    #     LT 3: Using Basic HTTP
    #    

    lt3 = LearningTool(full_name = u"UNED aLF (HTTP)", name = "uned",
                     url = u"https://www.innova.uned.es/")
    db_session.add(lt3)

    credential = BasicHttpCredentials(lt_login = 'uned', lt_password = password, lt = lt3, lt_url = 'http://localhost:5000/fake_list_courses/gateway4labs/list', labmanager_login = 'labmanager', labmanager_password = 'password')
    db_session.add(credential)

    lt_admin3   = LtUser(login="admin", full_name="Administrator", lt = lt3, access_level = 'admin')
    lt_admin3.password = password

    db_session.add(lt_admin3)

    permission_to_lt3 = PermissionToLt(lt = lt3, laboratory = robot_lab, configuration = '', local_identifier = 'robot')
    db_session.add(permission_to_lt3)

    course1 = Course(name = "Physics course", lt = lt3, context_id = "physics")
    course2 = Course(name = "Robots course", lt = lt3, context_id = "robots")
    db_session.add(course1)
    db_session.add(course2)

    permission_to_course = PermissionToCourse(course = course2, permission_to_lt = permission_to_lt3)
    db_session.add(permission_to_course)

    #######################################################
    #     
    #     LT 4: Using Shindig, school 1
    #    

    lt4 = LearningTool(full_name = u"School 1 at Graasp", name = "school1", url = u"http://graasp.epfl.ch/")
    db_session.add(lt4)

    credential = ShindigCredentials(lt = lt4, shindig_url = 'http://shindig.epfl.ch')
    db_session.add(credential)

    lt_admin4   = LtUser(login="admin", full_name="Administrator", lt = lt4, access_level = 'admin')
    lt_admin4.password = password

    db_session.add(lt_admin4)

    permission_to_lt4 = PermissionToLt(lt = lt4, laboratory = robot_lab, configuration = '', local_identifier = 'robot')
    db_session.add(permission_to_lt4)

    course1 = Course(name = "Physics course", lt = lt4, context_id = "1234")
    course2 = Course(name = "Robots course", lt = lt4, context_id = "1235")
    db_session.add(course1)
    db_session.add(course2)

    permission_to_course = PermissionToCourse(course = course2, permission_to_lt = permission_to_lt4)
    db_session.add(permission_to_course)

    #######################################################
    #     
    #     LT 5: Using Shindig, school 2
    #    

    lt5 = LearningTool(full_name = u"School 2 at Graasp", name = "school2", url = u"http://graasp.epfl.ch/")
    db_session.add(lt5)

    credential = ShindigCredentials(lt = lt5, shindig_url = 'http://shindig.epfl.ch')
    db_session.add(credential)

    lt_admin5  = LtUser(login="admin", full_name="Administrator", lt = lt5, access_level = 'admin')
    lt_admin5.password = password

    db_session.add(lt_admin5)

    permission_to_lt5 = PermissionToLt(lt = lt5, laboratory = robot_lab, configuration = '', local_identifier = 'robot')
    db_session.add(permission_to_lt5)

    course1 = Course(name = "Other physics course", lt = lt5, context_id = "1236")
    course2 = Course(name = "Other robots course", lt = lt5, context_id = "1237")
    db_session.add(course1)
    db_session.add(course2)

    permission_to_course = PermissionToCourse(course = course2, permission_to_lt = permission_to_lt5)
    db_session.add(permission_to_course)

    db_session.commit()
