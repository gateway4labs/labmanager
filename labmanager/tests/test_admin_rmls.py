# -*-*- encoding: utf8 -*-*-

from flask import session
from labmanager.tests.util import G4lTestCase
from labmanager.tests.test_login_admin import BaseTestLogin
from flask.ext.testing import TestCase


class TestRegisterLabsAdmin(BaseTestLogin, G4lTestCase):
    login_path = '/login/admin/'
    logout_path = '/logout'
    username = 'admin'
    password = 'password'
    usertype = 'labmanager'

    def test_public_availability(self):
        rv = self.login(username=self.username, password=self.password)
        self.assert_200(rv)
        self.assertEquals(self.username, session['loggeduser'])
        rv = self.client.post('/admin/rlms/labs/lab/availability/public',
                              data=dict(lab_id=1, activate=False,
                                        public_identifier=""),
                              follow_redirects=True)
        self.assert_200(rv)
