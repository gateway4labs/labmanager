# -*-*- encoding: utf8 -*-*-

from flask import session
from sqlalchemy import sql
from labmanager.tests.util import G4lTestCase, BaseTestLogged
from flask.ext.testing import TestCase
from ..models import LabManagerUser
from labmanager.db import db


class MethodsCreateNewUser(BaseTestLogged):

    def test_route_create_new_user_work(self):
        rv = self.client.get(self.create_new_user_path, follow_redirects=True)
        self.assert_200(rv)

    def test_create_new_user_work(self):
        rv = self.client.post(self.create_new_user_path,
                              data=dict
                              (
                                  name="antonio",
                                  login="antonio",
                                  password="password"
                                  ),
                              follow_redirects=True)
        self.assert_200(rv)
        self.assertTrue(db.session.query(LabManagerUser).
                        filter_by(login='antonio').first() is not None,
                        "Error creating new user")
        rv = self.logout()
        self.assertNotIn("loggeduser", session)
        rv = self.login(username='antonio', password='password')
        self.assert_200(rv)
        self.assertEquals('antonio', session['loggeduser'])


class TestCreateNewUserAdmin(MethodsCreateNewUser, G4lTestCase):
    login_path = '/login/admin/'
    logout_path = '/logout'
    username = 'admin'
    password = 'password'
    usertype = 'labmanager'
    create_new_user_path = '/admin/users/labmanager/new/'

"""
class TestCreateNewUserLms(MethodsCreateNewUser, G4lTestCase):
    login_path = '/login/lms/'
    logout_path = '/logout'
    username = 'admin'
    password = 'password'
    usertype = 'lms'
    lt_name = 'lms'
    """
        #Use 1 because the name have associate a number.
        #For example Deusto have id = 1
"""
    lt_value = 1
    create_new_user_path = '/lms_admin/users/new/'


class TestCreateNewUserPle(MethodsCreateNewUser, G4lTestCase):
    login_path = '/login/ple/'
    logout_path = '/logout'
    username = 'admin'
    password = 'password'
    usertype = 'lms'
    lt_name = 'lms'
    """ 
    #Use 5 because the name have associate a number.
    #    For example School have id = 5
"""
    lt_value = 5
    create_new_user_path = '/ple_admin/users/new/'
"""

