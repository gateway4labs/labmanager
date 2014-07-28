# -*-*- encoding: utf8 -*-*-

from flask import session
from labmanager.tests.util import G4lTestCase
from flask.ext.testing import TestCase


class BaseTestLogin(G4lTestCase):
    lt_name = 'lms'
    lt_value = 'deusto'

    def setUp(self):
        super(BaseTestLogin, self).setUp()
        self.client.__enter__()

    def tearDown(self):
        self.client.__exit__(None, None, None)
        super(BaseTestLogin, self).tearDown()

    def login(self, redirect=True, **kwargs):
        kwargs[self.lt_name] = self.lt_value
        return self.client.post(self.login_path, data=kwargs,
                                follow_redirects=redirect)

    def logout(self):
        return self.client.get(self.logout_path, follow_redirects=True)

class MethodsLogin(BaseTestLogin):

    def test_login_admin_works(self):
        rv = self.login(username=self.username, password=self.password)
        print session['loggeduser']
        print "hello"
        #self.assert_200(rv)
        #self.assertEquals('admin', session['loggeduser'])
        #self.assertEquals('labmanager', session['usertype'])
    """
    def test_login_admin_fails_wrong_form(self):
        rv = self.login(does_not_exist="admin", password="password")
        self.assert_200(rv)
        self.assertNotIn("loggeduser", session)

    def test_login_admin_fails_wrong_user(self):
        rv = self.login(username="wrong_user", password="password")
        self.assert_200(rv)
        self.assertNotIn("loggeduser", session)

    def test_login_admin_fails_wrong_password(self):
        rv = self.login(username="wrong_user", password="1235490295921399213")
        self.assert_200(rv)
        self.assertNotIn("loggeduser", session)

    def test_login_admin_work_with_utf8(self):
        rv = self.login(username="admin", password="utf8_char_ñ")
        self.assert_200(rv)
        self.assertNotIn("loggeduser", session)

    def test_logout_admin_work(self):
        rv = self.login(username="admin", password="password")
        self.assertIn("loggeduser", session)
        rv = self.logout()
        self.assertNotIn("loggeduser", session)

    def test_logout_admin_fails(self):
        rv = self.logout()
        self.assert_401(rv)

    def test_login_work_redirect_work(self):
        rv = self.login(username="admin", password="password", redirect=False)
        self.assert_redirects(rv, '/admin/')

    def test_login_fail_redirect(self):
        rv = self.login(username="wrong_user",
                        password="password", redirect=False)
        self.assertNotEqual(rv.status_code, 302)
        self.assertNotEqual(rv.location, "http://localhost/admin/")
    """
class TestLoginAdmin(MethodsLogin):
    login_path = '/login/admin/'
    logout_path = '/logout'
    username = 'admin'
    password = 'password'

    

"""
class TestLoginLms(BaseTestLogin, G4lTestCase):
    login_path = '/login/lms/'
    logout_path = '/logout'

"""

"""
class TestLoginPle(BaseTestLogin, G4lTestCase):
    login_path = '/login/ple/'
    logout_path = '/logout/'
    lt_name = 'ple'
    lt_value = 'school1'
"""
