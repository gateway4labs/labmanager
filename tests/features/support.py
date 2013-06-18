import hashlib
from labmanager.db import db_session
import labmanager.models as models

from lettuce import step, world
from lettuce_webdriver import webdriver

def create_admin(username, password):
    password = unicode(hashlib.new('sha', password).hexdigest())
    admin =  models.LabManagerUser.new(login = username,
        name = 'Administrator',
        password = password,
        access_level ='admin')

def create_lms(name=u'LMS Name', url=u'http://example.com'):
    return models.LMS.new(name=name, url=url)

def add_oauth_to_lms(lms, lms_login=u'shared', password=u'secret'):
    return \
    models.Credential.new(lms_login=lms_login, password=password, lms=lms)

def fill_in_lms_fields(step, name, url):
    step.given('I click "LMS Management"')
    step.given('I click "LMS"')
    step.given('I click "Create"')
    step.given('I fill in "name" with "%s"' % name)
    step.given('I fill in "url" with "%s"' % url)
    step.given('I click "Add Authentications"')
    # print world.browser.page_source
    step.given('I fill in "authentications-0-lms_login" with "shared"')
    step.given('I fill in "authentications-0-password" with "secret"')
