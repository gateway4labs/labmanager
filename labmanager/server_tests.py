import os
import json
import unittest
import tempfile

from werkzeug import Headers

import labmanager.server as server
from labmanager.database import add_sample_users

class FlaskrTestCase(unittest.TestCase):

    def setUp(self):
        """Before each test, set up a blank database"""
        self.db_fd, server.app.config['DATABASE'] = tempfile.mkstemp()
        server.app.config['TESTING'] = True
        self.app = server.app.test_client()
        add_sample_users()
        self.headers = Headers([ ['AUTHORIZATION', 'BASIC ' + 'deusto:password'.encode('base64')] ])

    def tearDown(self):
        """Get rid of the database again after each test."""
        os.close(self.db_fd)
        os.unlink(server.app.config['DATABASE'])

#    def login(self, username, password):
#        return self.app.post('/login', data=dict(
#            username=username,
#            password=password
#        ), follow_redirects=True)
#
#    def logout(self):
#        return self.app.get('/logout', follow_redirects=True)

    # testing functions

    def test_empty_db(self):
        """Start with a blank database."""

        rv = self.app.post('/lms4labs/requests/', data = json.dumps({
            'courses'      : [1,2,3],
            'request'      : "the payload",
            'general-role' : "admin",
            'author'       : "pablo"
        }), headers = self.headers, content_type = "application/json")

        assert 'Hi lms' in rv.data

if __name__ == '__main__':
    unittest.main()
