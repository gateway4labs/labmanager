# -*- coding: utf-8 -*-
from lettuce import step

@step(u'Given a LMS with \'([^\']*)\' public and \'([^\']*)\' secret keys')
def given_a_lms_with_group1_public_and_group2_secret_keys(step, shared, secret):
    # LMS.create(shared: shared, secret: secret)
    assert False, 'This step must be implemented'

@step(u'I authenticate with \'([^\']*)\' and \'([^\']*)\'')
def when_i_authenticate_with_group1_and_group2(step, secret, signature):
    assert False, 'This step must be implemented'

@step(u'I should be authenticated')
def then_i_should_be_authenticated(step):
    # session['consumer'] is not None
    assert False, 'This step must be implemented'

@step(u'Given no LMS')
def given_no_lms(step):
    assert False # no-op

@step(u'I should get a "([^"]*)" http code')
def then_i_should_get_a_group1_http_code(step, http_code):
    # response.code.should eql(int(http_code))
    assert False, 'This step must be implemented'
