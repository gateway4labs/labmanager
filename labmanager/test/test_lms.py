# -*-*- encoding: utf-8 -*-*-
import os
import sys
import json
import unittest
import tempfile

from bs4 import BeautifulSoup

from werkzeug import Headers

sys.path.append('.')
os.environ['TESTING_LABMANAGER'] = 'sqlite:///:memory:'

from labmanager.test.fake_rlms import register_fake, LAB_NAME, LAB_ID
register_fake()

import labmanager as server
from labmanager.database import add_sample_users
from labmanager.views.admin.rlms import RLMSPanel

ADMIN = 'admin'
PASSWORD = 'password'

LOCAL_ID = 'localid'

LMS_NAME = 'Testing LMS'
LMS_URL  = 'http://localhost:31337/'
LMS_PASSWORD = 'lms_password'

COURSE_NAME = 'My course'
CONTEXT_ID  = 'context-id'

RLMS_KIND     = 'FakeRLMS<>1.0'
RLMS_LOCATION = 'Bilbao'
RLMS_URL      = 'http://github.com/lms4labs/labmanager/'

SELECTION_COLUMNS = 2 # Number of columns used by flask-admin for selection, deleting or editing

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

    def add_course(self, lms_name = LMS_NAME, course_name = COURSE_NAME, context_id = CONTEXT_ID):
        rv = self.app.get('/admin/lms/courses/new/', follow_redirects = True)
        data = self._parse_selects(rv.data)

        lms_id = self._find_in_select(data, 'lms', lms_name)

        request_data = dict( lms = lms_id,  name = course_name, context_id = context_id)
        self.app.post('/admin/lms/courses/new/', data = request_data, follow_redirects = True)

    def add_rlms(self, kind = RLMS_KIND, location = RLMS_LOCATION, url = RLMS_URL):
        data = dict(kind = kind, location = location, url = url)
        rv = self.app.post('/admin/rlms/rlms/new/?rlms=FakeRLMS<>1.0', data=data, follow_redirects = True)

    def add_lab(self, rlms_kind = RLMS_KIND):
        rv = self.app.get('/admin/rlms/rlms/', follow_redirects = True)
        table = self._parse_tables(rv.data)[0]

        version_index = RLMSPanel.column_list.index('version') + SELECTION_COLUMNS
        kind_index    = RLMSPanel.column_list.index('kind')    + SELECTION_COLUMNS

        for row in table:
            rlms_kind, rlms_version = RLMS_KIND.split('<>')
            cur_kind    = row[kind_index].get_text()
            cur_version = row[version_index].get_text()
            if cur_version == rlms_version and cur_kind == rlms_kind:
                lab_url = row[-1].find_all('a')[0].get('href')
                break
        
        data = { LAB_ID   : u'on', 'action' : u'register' }
        rv = self.app.post(lab_url, data=data, follow_redirects = True)
        table = self._parse_tables(rv.data)[0]
        return lab_url

    def add_permission_to_lms(self, lms_name = LMS_NAME, lab_name = LAB_NAME, local_id = LOCAL_ID):
        rv = self.app.get('/admin/permissions/lms/new/', follow_redirects = True)
        data = self._parse_selects(rv.data)

        lab_id = self._find_in_select(data, 'laboratory', lab_name)
        lms_id = self._find_in_select(data, 'lms', lms_name)

        request_data = {
            'laboratory'       : lab_id, 'lms'              : lms_id,
            'configuration'    : '',     'local_identifier' : local_id,
        }
        self.app.post('/admin/permissions/lms/new/', data = request_data, follow_redirects = True)

    def add_permission_to_course(self, local_id = LOCAL_ID, course_name = COURSE_NAME):
        rv = self.app.get('/admin/permissions/course/new/', follow_redirects = True)

        selects_data         = self._parse_selects(rv.data)
        permission_on_lab_id = self._find_in_select(selects_data, 'permission_on_lab', local_id)
        course_id            = self._find_in_select(selects_data, 'course', course_name)
        
        request_data = {
            'permission_on_lab' : permission_on_lab_id, 'course' : course_id,
            'access'            : 'granted',            'configuration' : '',
        }

        self.app.post('/admin/permissions/course/new/', data = request_data, follow_redirects = True)
        

    def _find_in_select(self, select_data, select_name, pattern):
        for value, name in select_data[select_name]:
            if pattern in name:
                return value
        raise AssertionError('Pattern %s not found in %s' % (pattern, select_data[select_name]))
    
    def _parse_selects(self, html):
        """ Returns a dictionary with the <select found in the HTML document """
        parsed = BeautifulSoup(html)
        select_data = {}
        for select in parsed.find_all('select'):
            name = select.get('name')
            values = []
            for option in select.find_all('option'):
                text  = option.get_text()
                value = option.get('value')
                values.append((value, text))
            select_data[name] = values
        return select_data

    def _parse_tables(self, html):
        parsed = BeautifulSoup(html)
        tables = []
        for table in parsed.find_all('table'):
            cur_table = []
            rows = table.find_all('tr')
            for row in rows:
                columns = row.find_all('td')
                if columns:
                    cur_table.append(columns)
            tables.append(cur_table)
        return tables

class LabmanagerTestCase(unittest.TestCase):

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

    def _check_course(self, name = COURSE_NAME):
        rv = self.app.get('/admin/lms/courses/')
        assert name in rv.data

    def _check_rlms(self, location = RLMS_LOCATION, url = RLMS_URL):
        rv = self.app.get('/admin/rlms/rlms/')
        assert location in rv.data 
        assert url in rv.data

    def _check_labs_in_rlms(self, lab_url, lab_name = LAB_NAME, lab_id = LAB_ID):
        rv = self.app.get('/admin/rlms/labs/')
        assert lab_name in rv.data
        assert lab_id in rv.data

    def _check_local_id_in_lms_permissions(self, local_id = LOCAL_ID):
        rv = self.app.get('/admin/permissions/lms/')
        assert local_id in rv.data

    def _check_local_id_in_course_permissions(self, local_id = LOCAL_ID):
        rv = self.app.get('/admin/permissions/course/')
        assert local_id in rv.data

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
        lab_url = self.proxy.add_lab()
        self._check_labs_in_rlms(lab_url)
    
    def test_add_permission_to_lms(self):
        self.login()
        self.proxy.add_rlms()
        self.proxy.add_lab()
        self.proxy.add_lms()
        self.proxy.add_permission_to_lms()
        self._check_local_id_in_lms_permissions()

    def test_add_course(self):
        self.login()
        self.proxy.add_lms()
        self.proxy.add_course()
        self._check_course()

    def test_add_permission_to_course(self):
        self.login()
        self.proxy.add_rlms()
        self.proxy.add_lab()
        self.proxy.add_lms()
        self.proxy.add_course()
        self.proxy.add_permission_to_lms()
        self.proxy.add_permission_to_course()
        self._check_local_id_in_course_permissions()
       

    # testing functions
    def test_lms_request(self):
        self.login()

        # 1. Add the RLMS
        self.proxy.add_rlms()

        # 2. Add the laboratory for that RLMS
        self.proxy.add_lab()

        # 3. Add the LMS
        self.proxy.add_lms()
    
        # 4. Add a permission to that LMS
        self.proxy.add_permission_to_lms()

        # 5. Add a course
        self.proxy.add_course()

        # 6. Add a permission on that course
        self.proxy.add_permission_to_course()
        
        # 7. Perform a request
        rv = self.app.post('/lms4labs/requests/', data = json.dumps({
            'courses'        : { "1" : ["student"], "2" : ["teacher"] },
            'request-payload': "the payload",
            'general-role'   : "admin",
            'author'         : "pablo",
            'complete-name'  : "Pablo Orduña",
        }), headers = self.headers, content_type = "application/json")

        # 8. Validate the request
        print rv.data
        
        # kthxbai
        self.logout()


if __name__ == '__main__':
    unittest.main()