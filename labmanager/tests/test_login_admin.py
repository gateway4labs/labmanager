from flask import Flask, session
from labmanager.tests.util import G4lTestCase

class TestLoginAdmin(G4lTestCase):
        
    def login(self, username, password, redirect = True):
        return self.client.post('/login/admin/', data=dict(login = username, password = password), follow_redirects = redirect)

    def logout(self):
        return self.client.get('/logout', follow_redirects = True)

    def test_login_works(self):
        #rv1 = self.client.logout()
        #assert "logged_in" not in session or not session["logged_in"]
        rv = self.login('admindfsfs', 'password')
        #self.assert_200(rv)
        assert rv.status_code == 200
        #assert session["loggeduser"] == "admin"
        #assert session['last_request'] = time()
        #assert session['usertype'] == 'labmanager'
        #assert session["logged_in"] == True
        #assert session["login"] == "testuser"
        #assert session["name"] == "Test User"
        #assert "Invalid username."