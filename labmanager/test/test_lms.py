# -*-*- encoding: utf-8 -*-*-
import os
import sys
import json
import unittest
import tempfile

from werkzeug import Headers

sys.path.append('.')
os.environ['TESTING_LABMANAGER'] = 'sqlite:///:memory:'

from labmanager.test.fake_rlms import register_fake, LAB_NAME, LAB_ID
register_fake()

import labmanager as server
from labmanager.database import add_sample_users

ADMIN = 'admin'
PASSWORD = 'password'

LMS_NAME = 'Testing LMS'
LMS_URL  = 'http://localhost:31337/'
LMS_PASSWORD = 'lms_password'

RLMS_KIND     = 'FakeRLMS<>1.0'
RLMS_LOCATION = 'Bilbao'
RLMS_URL      = 'http://github.com/lms4labs/labmanager/'

class RequestProxy(object):

    def __init__(self, app):
        self.app = app

    def add_lms(self, name = LMS_NAME, url = LMS_URL, authentications = None):
        if authentications is None:
            authentications = [ dict(key = '', secret = LMS_PASSWORD, kind = 'Basic') ]
        
        data = dict(name = name, url = url)
        for pos, auth_config in enumerate(authentications):
            for key in 'key', 'secret', 'kind':
                data['autentications-%s-%s' % (pos, key)] = auth_config[key]

        self.app.post('/admin/lms/lms/new/', data=data, follow_redirects = True)

    def add_rlms(self, kind = RLMS_KIND, location = RLMS_LOCATION, url = RLMS_URL):
        data = dict(kind = kind, location = location, url = url)
        rv = self.app.post('/admin/rlms/rlms/new/?rlms=FakeRLMS<>1.0', data=data, follow_redirects = True)

    def add_lab(self):
        pass

class FlaskrTestCase(unittest.TestCase):

    def setUp(self):
        """Before each test, set up a blank database"""
        server.app.config['TESTING'] = True
        server.app.config['CSRF_ENABLED'] = False
        self.app = server.app.test_client()
        self.proxy = RequestProxy(self.app)
        add_sample_users()
        self.headers = Headers([ ['AUTHORIZATION', 'BASIC ' + 'deusto:password'.encode('base64')] ])


    def login(self, username = 'admin', password = 'password'):
        return self.app.post('/login', data=dict(
            username=username,
            password=password
        ), follow_redirects=True)

    def logout(self):
        return self.app.get('/logout', follow_redirects=True)

    def _check_lms(self, name = LMS_NAME):
        rv = self.app.get('/admin/lms/lms/')
        assert name in rv.data

    def _check_rlms(self, location = RLMS_LOCATION, url = RLMS_URL):
        rv = self.app.get('/admin/rlms/rlms/')
        assert location in rv.data 
        assert url in rv.data

    def _check_labs_in_rlms(self, lab_name = LAB_NAME, lab_id = LAB_ID):
        rv = self.app.get('/admin/???')
        assert lab_name in rv.data
        assert lab_id in rv.data

    def test_add_lms(self):
        self.login()
        self.proxy.add_lms()
        self._check_lms()
        self.logout()

    def test_add_rlms(self):
        self.login()
        self.proxy.add_rlms()
        self._check_rlms()
        self.logout()

    def test_add_lab(self):
        self.login()
        self.proxy.add_rlms()
        self._check_labs_in_rlms()
        self.proxy.add_lab()
        
        
    # testing functions
    def test_lms_request(self):
        """Start with a blank database."""

        self.login()

        self.proxy.add_lms()
        self.proxy.add_rlms()
        
        #
        # TODO: add laboratory, add permission on laboratory, add course, add permission on course
        # 
        rv = self.app.post('/lms4labs/requests/', data = json.dumps({
            'courses'        : { "1" : ["student"], "2" : ["teacher"] },
            'request-payload': "the payload",
            'general-role'   : "admin",
            'author'         : "pablo",
            'complete-name'  : "Pablo Orduña",
        }), headers = self.headers, content_type = "application/json")

        self.logout()


if __name__ == '__main__':
    unittest.main()
