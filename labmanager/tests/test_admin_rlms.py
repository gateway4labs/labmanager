# -*-*- encoding: utf8 -*-*-

from flask import session
from labmanager.tests.util import G4lTestCase, BaseTestLogged
from flask.ext.testing import TestCase
from labmanager.models import Laboratory
from labmanager.db import db
from sqlalchemy.exc import StatementError


PUBLIC_AVAILABILITY_MSG_ERROR = "Public identifier &#39;1&#39; already exists"
PUBLIC_AVAILABILITY_EMPTY_MSG_ERROR = "Invalid public identifier (empty)"
LOCAL_AVAILABILITY_MSG_ERROR = "Local identifier &#39;1&#39; already exists"
LOCAL_AVAILABILITY_EMPTY_MSG_ERROR = "Invalid local identifier (empty)"


class BaseTestRegisterLabsAdmin(BaseTestLogged):
    login_path = '/login/admin/'
    logout_path = '/logout'
    username = 'admin'
    password = 'password'
    usertype = 'labmanager'
    identifier_name = None

    def query(self):
        kwargs = {self.identifier_name: 1}
        return len(db.session.query(Laboratory).filter_by(**kwargs).all()) > 0

    def make_available(self, redirect=True, identifier_value="", **kwargs):
        kwargs[self.identifier_name] = identifier_value
        return self.client.post(self.availability_path,
                                data=kwargs, follow_redirects=redirect)

    def test_availability_work(self):
        self.assertFalse(self.query(),
                         "Error to make lab in mode availability")
        rv = self.make_available(identifier_value="1",
                                 lab_id=1, activate="false")
        self.assert_200(rv)
        self.assertTrue(self.query(), "Error to make lab in mode availability")

    def test_availability_fail_empty(self):
        rv = self.make_available(identifier_value="",
                                 lab_id=1, activate="false")
        self.assert_200(rv)
        self.assertIn(self.availability_empty_msg_error, rv.data)

    def test_availability_fail_only_blanks(self):
        rv = self.make_available(identifier_value="           ",
                                 lab_id=1, activate="false")
        self.assert_200(rv)
        self.assertIn(self.availability_empty_msg_error, rv.data)

    def test_availity_fail_duplicate(self):
        rv = self.make_available(identifier_value="1",
                                 lab_id=1, activate="false")
        kwargs = {self.identifier_name: 1}
        self.assert_200(rv)
        self.assertTrue(self.query(), "Error to make lab in mode availability")
        rv = self.make_available(identifier_value="1",
                                 lab_id=2, activate="false")
        self.assertIn(self.availability_msg_error, rv.data)

    def test_make_not_available(self):
        kwargs = {self.identifier_name: 1}
        self.assertFalse(self.query(),
                         "Error to make lab in mode availability")
        rv = self.make_available(identifier_value="1",
                                 lab_id=1, activate="false")
        self.assert_200(rv)
        self.assertTrue(self.query(), "Error to make lab in mode availability")
        rv = self.make_available(identifier_value="1",
                                 lab_id=1, activate="true")
        self.assert_200(rv)
        self.assertFalse(self.query(),
                         "Error to make lab in mode not availability")

    def test_redirect_availability_work(self):
        kwargs = {self.identifier_name: 1}
        self.assertFalse(self.query(),
                         "Error to make lab in mode availability")
        rv = self.make_available(identifier_value="1",
                                 lab_id=1, activate="false", redirect=False)
        self.assertTrue(self.query(), "Error to make lab in mode availability")
        self.assert_redirects(rv, '/admin/rlms/labs/')

    def test_redirect_availability_fail_empty(self):
        rv = self.make_available(identifier_value="",
                                 lab_id=1, activate="false", redirect=False)
        self.assert_redirects(rv, '/admin/rlms/labs/')

    def test_redirect_availability_fail_duplicate(self):
        rv = self.make_available(identifier_value="1",
                                 lab_id=1, activate="false")
        kwargs = {self.identifier_name: 1}
        self.assert_200(rv)
        self.assertTrue(self.query(), "Error to make lab in mode availability")
        rv = self.make_available(identifier_value="1",
                                 lab_id=2, activate="false", redirect=False)
        self.assert_redirects(rv, '/admin/rlms/labs/')

    def test_redirect_make_not_available(self):
        kwargs = {self.identifier_name: 1}
        self.assertFalse(self.query(),
                         "Error to make lab in mode availability")
        rv = self.make_available(identifier_value="1",
                                 lab_id=1, activate="false")
        self.assert_200(rv)
        self.assertTrue(self.query(), "Error to make lab in mode availability")
        rv = self.make_available(identifier_value="1",
                                 lab_id=1, activate="true", redirect=False)
        self.assertFalse(self.query(),
                         "Error to make lab in mode not availability")
        self.assert_redirects(rv, '/admin/rlms/labs/')


class TestRegisterLabsAdminAvailabilityLocal(BaseTestRegisterLabsAdmin,
                                             G4lTestCase):
    availability_path = '/admin/rlms/labs/lab/availability/local'
    identifier_name = 'default_local_identifier'
    availability_msg_error = LOCAL_AVAILABILITY_MSG_ERROR
    availability_empty_msg_error = LOCAL_AVAILABILITY_EMPTY_MSG_ERROR


class TestRegisterLabsAdminAvailabilityPublic(BaseTestRegisterLabsAdmin,
                                              G4lTestCase):
    availability_path = '/admin/rlms/labs/lab/availability/public'
    identifier_name = 'public_identifier'
    availability_msg_error = PUBLIC_AVAILABILITY_MSG_ERROR
    availability_empty_msg_error = PUBLIC_AVAILABILITY_EMPTY_MSG_ERROR
