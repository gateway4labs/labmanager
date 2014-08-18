# -*-*- encoding: utf8 -*-*-

from flask import session
from sqlalchemy import sql
from labmanager.tests.util import G4lTestCase, BaseTestLogged
from flask.ext.testing import TestCase
from ..models import LabManagerUser
from labmanager.db import db


class MethodsCreateNewUser(BaseTestLogged):
    """

    def test_route_create_new_user_work(self):
        rv = self.client.get(self.create_new_user_path,follow_redirects=True)
        self.assert_200(rv)
    """

    def test_create_new_user_work(self):
        rv = self.client.post(self.create_new_user_path, data=dict(name="antonio",login="antonio",password="123456789"), follow_redirects=True)
        #self.assert_200(rv)
        #print LabManagerUser.exists('tusmuertos', 'password')
        print db.session.query(LabManagerUser).filter_by(login='admin').first()
        print db.session.query(LabManagerUser).filter_by(login='antonio').first()
        #self.assert_redirects(rv, '/admin/users/labmanager/new/?url=%2Fadmin%2Fusers%2Flabmanager%2F')
        print rv.data
        """
        print LabManagerUser.exists('tusmuertos', 'password')
        self.assertIn("loggeduser", session)
        print "aquoi"
        print session['loggeduser']
        rv = self.logout()
        self.assertNotIn("loggeduser", session)
        rv = self.login(username='tusmuertos', password='password')
        self.assert_200(rv)
        print rv
        print "aqui"
        print session['loggeduser']
        self.assertEquals('prueba', session['loggeduser'])
        self.assertEquals(self.usertype, session['usertype'])
        """

class TestCreateNewUserAdmin(MethodsCreateNewUser, G4lTestCase):
    login_path = '/login/admin/'
    logout_path = '/logout'
    username = 'admin'
    password = 'password'
    usertype = 'labmanager'
    create_new_user_path = '/admin/users/labmanager/new/'


