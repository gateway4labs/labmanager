# -*- coding: utf-8 -*-

from lettuce import step, world
from lettuce_webdriver import webdriver

import support

@step(u'I add an [Oo]auth LMS with name "([^"]*)" and url "([^"]*)"')
def when_i_add_an_oauth_lms_with_name_group1_and_url_group2(step, name, url):
    support.fill_in_lms_fields(step, name, url)
    step.given('I press "Submit"')

@step(u'I visit the LMS list page')
def and_i_visit_the_lms_list_page(step):
    print "HELLO!!"
    world.browser.get('http://localhost:5001/admin/lms/lms/')

@step(u'an? OAuth LMS with name "([^"]*)" and url "([^"]*)"')
def create_oauth_lms(step, name, url):
    lms = support.create_lms(name, url)
    support.add_oauth_to_lms(lms)

@step(u'add an? basic auth LMS with name "([^"]*)" and url "([^"]*)"')
def when_i_add_an_oauth_lms_with_name_group1_and_url_group2(step, name, url):
    support.fill_in_lms_fields(step, name, url)
    step.given('I select "Basic" from "authentications-0-kind"')
    step.given('I press "Submit"')

@step(u'An? OAuth LMS with public key "([^"]*)" and private key "([^"]*)"')
def given_an_oauth_lms_with_public_key_group1_and_private_key_group2(step, shared, secret):
    assert False, 'This step must be implemented'

@step(u'an? experiment named "([^"]*)" exists')
def and_an_experiment_named_group1(step, name):
    assert False, 'This step must be implemented'

@step(u'LMS "([^"]*)" has permission to access "([^"]*)"')
def and_lms_group1_has_permission_to_access_group2(step, lms_shared, exp_name):
    assert False, 'This step must be implemented'

@step(u'I? reserve "([^"]*)" as "([^"]*)"')
def when_i_reserve_group1_as_group2(step, exp_name, lms_shared):
    assert False, 'This step must be implemented'

@step(u'experiment "([^"]*)" should be reserved')
def then_the_experiment_should_be_reserved(step, exp_name):
    assert False, 'This step must be implemented'
