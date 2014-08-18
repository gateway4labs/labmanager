# -*-*- encoding: utf8 -*-*-

from flask import session
from labmanager.tests.util import G4lTestCase, BaseTestLogged
from flask.ext.testing import TestCase


class MethodsCreateNewUser(BaseTestLogged):

    def test_route_create_new_user_work(self):
        rv = self.client.get(self.create_new_user_path)
        self.assert_200(rv)


class TestCreateNewUserAdmin(MethodsCreateNewUser, G4lTestCase):
    login_path = '/login/admin/'
    logout_path = '/logout'
    username = 'admin'
    password = 'password'
    usertype = 'labmanager'
    create_new_user_path = '/admin/users/labmanager/new/'


class TestCreateNewUserLms(MethodsCreateNewUser, G4lTestCase):
    login_path = '/login/lms/'
    logout_path = '/logout'
    username = 'admin'
    password = 'password'
    usertype = 'lms'
    lt_name = 'lms'
    """
        Use 1 because the name have associate a number.
        For example Deusto have id = 1
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
    """ Use 5 because the name have associate a number.
        For example School have id = 5
    """
    lt_value = 5
    create_new_user_path = '/ple_admin/users/new/'
