# -*-*- encoding: utf8 -*-*-

from flask import session
from labmanager.tests.util import G4lTestCase
from flask.ext.testing import TestCase
from labmanager.models import LtUser, LearningTool
from labmanager.db import db

class testRegisterGraasp(G4lTestCase):
    path = '/opensocial/register/'

    
    def test_route_register_graasp_work(self):
        rv = self.client.get(self.path)
        self.assert_200(rv)
    
    def test_register_work(self):
        rv =self.client.post(self.path, data=dict(full_name='example', short_name='expl', url='http://www.example.com', user_full_name='admin', user_login='admin1', user_password='password'),follow_redirects=True)
        #self.assert_200(rv)
        b = db.session.query(LearningTool).filter_by(full_name = 'example').first()
        a = db.session.query(LtUser).filter_by(login='admin1').first()
        print b
        print a.login
        #print rv.data