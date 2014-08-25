import unittest

from labmanager.models import RLMS, LabManagerUser

class ModelsReprTest(unittest.TestCase):
    def assert_repr(self, obj):
        representation = repr(obj)
        try:
            new_obj = eval(representation)
        except Exception as e:
            self.fail("Invalid representation: %s. Caused error: %s" % (representation, e))
        else:
            new_representation = repr(new_obj)
            self.assertEquals(representation, new_representation)

    def test_labmanager_user(self):
        labmanager_user = LabManagerUser(login = 'admin', name = 'Administrator', password = 'l33t')
        self.assert_repr(labmanager_user)

    def test_rlms(self):
        rlms = RLMS(kind = u'Super cool RLMS', location = u'World', url = u'http://foo/', version = u'3.1415', configuration = u'{}', publicly_available = True, public_identifier = u'yeah')
        self.assert_repr(rlms)
