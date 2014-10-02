from flask import Flask, session
from flask.ext.testing import TestCase
from labmanager import app
from labmanager.sample_data import add_sample_users
from labmanager.db import db


class G4lTestCase(TestCase):
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    TESTING = True

    def create_app(self):
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
        app.config['TESTING'] = True
        app.config['CSRF_ENABLED'] = False
        return app

    def setUp(self):
        add_sample_users(silence=True)

    def tearDown(self):
        db.drop_all()
        db.session.remove()


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


class BaseTestLogged(BaseTestLogin):

    def setUp(self):
        super(BaseTestLogged, self).setUp()
        rv = self.login(username=self.username, password=self.password)
        self.assert_200(rv)
        self.assertEquals(self.username, session['loggeduser'])
        self.assertEquals(self.usertype, session['usertype'])
        return rv

    def tearDown(self):
        self.assertIn("loggeduser", session)
        rv = self.logout()
        self.assertNotIn("loggeduser", session)
        self.client.__exit__(None, None, None)
        super(BaseTestLogged, self).tearDown()
