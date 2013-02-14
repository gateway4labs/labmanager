from labmanager.database import db_session
import labmanager.models as models
import hashlib

def create_admin(username, password):
    password = unicode(hashlib.new('sha', password).hexdigest())
    admin =  models.LabManagerUser.new(login = username,
        name = 'Administrator',
        password = password,
        access_level ='admin')

def create_lms(name=u'LMS Name', url=u'http://example.com'):
    return models.LMS.new(name=name, url=url)

def add_oauth_to_lms(lms, shared=u'shared', secret=u'secret'):
    return \
    models.Credential.new(key=shared, secret=secret, lms=lms, kind=u'OAuth1.0')