# -*-*- encoding: utf8 -*-*-

from flask import session
from labmanager.tests.util import G4lTestCase, BaseTestLogged
from flask.ext.testing import TestCase
from labmanager.models import Laboratory
from labmanager.db import db
from sqlalchemy.exc import StatementError


AVAILABILITY_MSG_ERROR = "Public identifier &#39;&#39; already exists"
AVAILABILITY_EMPTY_MSG_ERROR = "Invalid public identifier (empty)"


class TestRegisterLabsAdmin(BaseTestLogged, G4lTestCase):
    login_path = '/login/admin/'
    logout_path = '/logout'
    username = 'admin'
    password = 'password'
    usertype = 'labmanager'

    def test_public_availability_work(self):
        rv = self.client.post('/admin/rlms/labs/lab/availability/public',
                              data=dict(lab_id=1, activate=False,
                                        public_identifier="1"),
                              follow_redirects=True)
        self.assert_200(rv)
        self.assertNotIn(AVAILABILITY_MSG_ERROR, rv.data)
        self.assertTrue(db.session.query(Laboratory).
                        filter_by(public_identifier=1).all(),
                        "Error to make lab in mode availability plublic")

    def test_public_availability_fail_empty(self):
        rv = self.client.post('/admin/rlms/labs/lab/availability/public',
                              data=dict(lab_id=1, activate=False,
                                        public_identifier=""),
                              follow_redirects=True)
        self.assert_200(rv)
        self.assertIn(AVAILABILITY_EMPTY_MSG_ERROR, rv.data)
