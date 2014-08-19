# -*-*- encoding: utf8 -*-*-

from flask import session
from labmanager.tests.util import G4lTestCase
from flask.ext.testing import TestCase

class testRegisterGraasp(G4lTestCase):
    path = '/opensocial/register/'

    def test_route_register_graasp_work(self):
        rv = self.client.get(self.path)
        self.assert_200(rv)
