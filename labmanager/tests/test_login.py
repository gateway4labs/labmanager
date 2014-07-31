# -*-*- encoding: utf8 -*-*-

from flask import session
from labmanager.tests.util import G4lTestCase
from flask.ext.testing import TestCase


class BaseTestLogin(object):

    lt_name = None
    lt_value = None

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

    def test_login_works(self):
        rv = self.login(username=self.username, password=self.password)
        self.assert_200(rv)
        self.assertEquals(self.username, session['loggeduser'])
        self.assertEquals(self.usertype, session['usertype'])

    def test_login_fails_wrong_form(self):
        rv = self.login(does_not_exist="admin", password=self.password)
        self.assert_200(rv)
        self.assertNotIn("loggeduser", session)

    def test_login_fails_wrong_user(self):
        rv = self.login(username="wrong_user", password=self.password)
        self.assert_200(rv)
        self.assertNotIn("loggeduser", session)

    def test_login_fails_wrong_password(self):
        rv = self.login(username="wrong_user", password="1235490295921399213")
        self.assert_200(rv)
        self.assertNotIn("loggeduser", session)

    def test_login_work_with_utf8(self):
        rv = self.login(username=self.username, password="utf8_char_ñ")
        self.assert_200(rv)
        self.assertNotIn("loggeduser", session)

    def test_logout_work(self):
        rv = self.login(username=self.username, password=self.password)
        self.assertIn("loggeduser", session)
        rv = self.logout()
        self.assertNotIn("loggeduser", session)

    def test_logout_fails(self):
        rv = self.logout()
        self.assert_401(rv)

    def test_login_work_redirect_work(self):
        rv = self.login(username=self.username,
                        password=self.password, redirect=False)
        self.assert_redirects(rv, self.route)

    def test_login_fail_redirect(self):
        rv = self.login(username="wrong_user",
                        password=self.password, redirect=False)
        self.assertNotEqual(rv.status_code, 302)
        self.assertNotEqual(rv.location, "http://localhost"+self.route)

    def test_login_lms_select_fail(self):
        if self.login_path != '/login/admin/':
            self.lt_value = 10000
            rv = self.login(username=self.username, password=self.password)
            self.assert_200(rv)
            self.assertNotIn("loggeduser", session)


class TestLoginAdmin(MethodsLogin, G4lTestCase):
    login_path = '/login/admin/'
    logout_path = '/logout'
    username = 'admin'
    password = 'password'
    usertype = 'labmanager'
    route = '/admin/'


class TestLoginLms(MethodsLogin, G4lTestCase):
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
    route = '/lms_admin/'


class TestLoginPle(MethodsLogin, G4lTestCase):
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
    route = '/ple_admin/'
