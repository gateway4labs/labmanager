# -*-*- encoding: utf8 -*-*-

from flask import session
from sqlalchemy import sql
from labmanager.tests.util import G4lTestCase, BaseTestLogged
from flask.ext.testing import TestCase
from ..models import LabManagerUser, LearningTool, LtUser
from labmanager.db import db
import unittest

class MethodsCreateNewUser(BaseTestLogged):

    access_level_name = None
    access_level_value = None

    def query(self, login_name):
        kwargs = {'login': login_name}
        if self.access_level_name is not None:
            lt = db.session.query(LearningTool).\
                filter_by(id=self.lt_value).first()
            kwargs = {'lt': lt}
        return db.session.query(self.db_model_user).filter_by(**kwargs).first()

    def test_route_create_new_user_work(self):
        rv = self.client.get(self.create_new_user_path, follow_redirects=True)
        self.assert_200(rv)

    def new_user(self, redirect=True, **kwargs):
        if self.access_level_name is not None:
                kwargs[self.access_level_name] = self.access_level_value
        return self.client.post(self.create_new_user_path, data=kwargs,
                                follow_redirects=redirect)

    def test_create_new_user_admin_work(self):
        kwargs = {}
        self.access_level_value = 'admin'
        kwargs[self.name_name] = 'example'
        kwargs['login'] = 'example'
        kwargs['password'] = 'password'
        rv = self.new_user(**kwargs)
        self.assert_200(rv)
        self.assertTrue(self.query('example') is not None,
                        "Error creating new user")
        rv = self.logout()
        self.assertNotIn("loggeduser", session)
        rv = self.login(username='example', password='password')
        self.assert_200(rv)
        self.assertEquals('example', session['loggeduser'])

    def test_create_new_user_instructor_work(self):
        kwargs = {}
        if self.access_level_name is not None:
            self.access_level_value = 'instructor'
            kwargs[self.name_name] = 'example'
            kwargs['login'] = 'example'
            kwargs['password'] = 'password'
            rv = self.new_user(**kwargs)
            self.assert_200(rv)
            self.assertTrue(self.query('example') is not None,
                            "Error creating new user")
            rv = self.logout()
            self.assertNotIn("loggeduser", session)
            rv = self.login(username='example', password='password')
            self.assert_200(rv)
            self.assertEquals('example', session['loggeduser'])
        else:
            pass

    @unittest.skip("Until #71 fixed")
    def test_create_new_user_admin_password_with_blanks_fail(self):
        kwargs = {}
        self.access_level_value = 'instructor'
        kwargs[self.name_name] = 'example'
        kwargs['login'] = 'example'
        kwargs['password'] = ' '
        rv = self.new_user(**kwargs)
        self.assert_200(rv)
        self.assertTrue(self.query('example') is None,
                        "Error creating user with blanks")
        """
        rv = self.logout()
        self.assertNotIn("loggeduser", session)
        rv = self.login(username='example', password=' ')
        self.assert_200(rv)
        #self.assertEquals('example', session['loggeduser'])
        self.assertNotIn("loggeduser", session)
        #rv = self.login(username='admin', password='password')
        """

class TestCreateNewUserAdmin(MethodsCreateNewUser, G4lTestCase):
    login_path = '/login/admin/'
    logout_path = '/logout'
    username = 'admin'
    password = 'password'
    usertype = 'labmanager'
    create_new_user_path = '/admin/users/labmanager/new/'
    access_level_name = None
    name_name = 'name'
    db_model_user = LabManagerUser


class TestCreateNewUserLms(MethodsCreateNewUser, G4lTestCase):
    login_path = '/login/lms/'
    logout_path = '/logout'
    username = 'admin'
    password = 'password'
    usertype = 'lms'
    lt_name = 'lms'
    # Use 1 because the name have associate a number.
    # For example Deusto have id = 1
    lt_value = 1
    create_new_user_path = '/lms_admin/users/new/'
    name_name = 'full_name'
    access_level_name = 'access_level'
    db_model_user = LtUser


class TestCreateNewUserPle(MethodsCreateNewUser, G4lTestCase):
    login_path = '/login/ple/'
    logout_path = '/logout'
    username = 'admin'
    password = 'password'
    usertype = 'lms'
    lt_name = 'lms'
    # Use 5 because the name have associate a number.
    # For example School have id = 5
    lt_value = 5
    create_new_user_path = '/ple_admin/users/new/'
    name_name = 'full_name'
    access_level_name = 'access_level'
    db_model_user = LtUser
