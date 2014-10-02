# -*-*- encoding: utf8 -*-*-

from flask import session
from labmanager.tests.util import G4lTestCase, BaseTestLogin
from flask.ext.testing import TestCase
from labmanager.models import LtUser, LearningTool
from labmanager.db import db


class testRegisterGraasp(BaseTestLogin, G4lTestCase):
    path = '/opensocial/register/'
    login_path = '/login/ple/'
    logout_path = '/logout'
    lt_name = 'lms'
    """ Use 6 because the name have associate a number.
        For example School have id = 5
    """
    lt_value = 6

    def register_in_graasp(self):
        rv = self.client.post(self.path, data=dict
                              (
                                  full_name='example',
                                  short_name='expl',
                                  url='http://www.example.com',
                                  user_full_name='admin',
                                  user_login='admin',
                                  user_password='password'
                              ),
                              follow_redirects=True)
        self.assert_200(rv)
        lt = db.session.query(LearningTool).\
            filter_by(full_name='example').first()
        query = db.session.query(LtUser).\
            filter_by(login='admin', lt=lt).first()
        self.assertTrue(query is not None,
                        "Error to save information in database")
        rv = self.login(username='admin', password='password')
        self.assert_200(rv)
        self.assertEquals('admin', session['loggeduser'])
        self.assertEquals('lms', session['usertype'])

    def test_route_register_graasp_work(self):
        rv = self.client.get(self.path)
        self.assert_200(rv)

    def test_register_work(self):
        self.register_in_graasp()

    def test_register_name_duplicate(self):
        self.register_in_graasp()
        rv = self.client.post(self.path, data=dict
                              (
                                  full_name='example1',
                                  short_name='expl',
                                  url='http://www.example.com',
                                  user_full_name='admin',
                                  user_login='admin',
                                  user_password='password'
                                  ),
                              follow_redirects=True)
        lt = db.session.query(LearningTool).\
            filter_by(full_name='example1', name='expl').first()
        query = db.session.query(LtUser).\
            filter_by(login='admin', lt=lt).first()
        self.assertTrue(query is None, "Error it must None")
        self.assert_200(rv)
        self.assertNotEqual(rv.location, "http://localhost"+self.path)

    def test_register_full_name_duplicate(self):
        self.register_in_graasp()
        rv = self.client.post(self.path, data=dict
                              (
                                  full_name='example',
                                  short_name='expl1',
                                  url='http://www.example.com',
                                  user_full_name='admin',
                                  user_login='admin',
                                  user_password='password'
                                  ),
                              follow_redirects=True)
        lt = db.session.query(LearningTool).\
            filter_by(full_name='example', name='expl1').first()
        query = db.session.query(LtUser).\
            filter_by(login='admin', lt=lt).first()
        self.assertTrue(query is None, "Error it must None")
        self.assert_200(rv)
        self.assertNotEqual(rv.location, "http://localhost"+self.path)
