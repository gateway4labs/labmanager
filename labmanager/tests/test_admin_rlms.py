# -*-*- encoding: utf8 -*-*-

from flask import session
from labmanager.tests.util import G4lTestCase
from labmanager.tests.test_login_admin import BaseTestLogin
from flask.ext.testing import TestCase
from labmanager.models import Laboratory
from labmanager.db import db
from sqlalchemy.exc import StatementError


msg_error = "Please check the flash error, \
this exception can raise if you change it"


class ExceptionAssertMsg:
    def __str__(self):
        return msg_error


class TestRegisterLabsAdmin(BaseTestLogin, G4lTestCase):
    login_path = '/login/admin/'
    logout_path = '/logout'
    username = 'admin'
    password = 'password'
    usertype = 'labmanager'

    def test_public_availability_work(self):
        rv = self.login(username=self.username, password=self.password)
        self.assert_200(rv)
        self.assertEquals(self.username, session['loggeduser'])
        rv = self.client.post('/admin/rlms/labs/lab/availability/public',
                              data=dict(lab_id=1, activate=False,
                                        public_identifier="1"),
                              follow_redirects=True)
        self.assert_200(rv)
        self.assertTrue(db.session.query(Laboratory).filter_by(public_identifier = 1).all(),"Error to make lab in mode availability plublic")
        
    def test_public_availability_fail(self):
        rv = self.login(username=self.username, password=self.password)
        self.assert_200(rv)
        public_identifier = ""
        self.assertEquals(self.username, session['loggeduser'])
        rv = self.client.post('/admin/rlms/labs/lab/availability/public',
                              data=dict(lab_id=1, activate=False,
                                        public_identifier=public_identifier),
                              follow_redirects=True)
        rv = self.client.post('/admin/rlms/labs/lab/availability/public',
                              data=dict(lab_id=2, activate=False,
                                        public_identifier=public_identifier),
                              follow_redirects=True)
        self.assert_200(rv)
        try:
            """
            assert "Public identifier '%s' already exists" % (public_identifier) in rv.data
            print "Public identifier '%s' already exists" % (public_identifier)
            I need put this " &#39;&#39; " to assert identify the content in public_identifier in this case is => ""
            """
            self.assertIn("Invalid public identifier (empty)", rv.data)
        except:
            raise ExceptionAssertMsg
