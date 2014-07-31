from flask import Flask
from labmanager.tests.util import G4lTestCase


class TestPublicLabs(G4lTestCase):
    def test_what(self):
        response = self.client.get('/public/labs/public/')
        self.assert_200(response)
