from flask.ext.testing import TestCase
from labmanager import app
from labmanager.sample_data import add_sample_users
from labmanager.db import db_session

class G4lTestCase(TestCase):
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    TESTING = True

    def create_app(self):
        return app

    def setUp(self):
        add_sample_users()

    def tearDown(self):
        db_session.remove()

