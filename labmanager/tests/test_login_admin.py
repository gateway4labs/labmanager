from flask import Flask, session
from labmanager.tests.util import G4lTestCase, app
from labmanager.views.authn import session

class TestLoginAdmin(G4lTestCase):
        
    def login(self, username, password, redirect = True):
        return self.client.post('/login/admin/', data=dict(login = username, password = password), follow_redirects = redirect)

    def logout(self):
        return self.client.get('/logout', follow_redirects = True)

    def test_login_works(self):
        #rv1 = self.client.logout()
        #assert "logged_in" not in session or not session["logged_in"]
        #with app.test_client() as c:
            #rv = c.get('/')
        rv = self.login('admin', 'password')
        self.assert_200(rv)
        print rv.data
        #esta linea es la que falla porque no tengo bien al variable session
        print session['loggeduser']
        #assert "Error in create_session" in rv.data
        rv = self.logout()
        #assert session["loggeduser"] == "admin"
        #assert session['last_request'] = time()
        #assert session['usertype'] == 'labmanager'
        #assert session["logged_in"] == True
        #assert session["login"] == "testuser"
        #assert session["name"] == "Test User"
        #assert "Invalid username."