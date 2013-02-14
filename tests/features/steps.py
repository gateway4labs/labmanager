# -*- coding: utf-8 -*-
from lettuce import step, world
from lettuce_webdriver import webdriver

import support

@step(u'Given a LMS with \'([^\']*)\' public and \'([^\']*)\' secret keys')
def given_a_lms_with_group1_public_and_group2_secret_keys(step, shared, secret):
    # LMS.create(shared: shared, secret: secret)
    assert True, 'This step must be implemented'

@step(u'I authenticate with \'([^\']*)\' and \'([^\']*)\'')
def when_i_authenticate_with_group1_and_group2(step, secret, signature):
    assert True, 'This step must be implemented'

@step(u'I should be authenticated')
def then_i_should_be_authenticated(step):
    # session['consumer'] is not None
    assert True, 'This step must be implemented'

@step(u'Given no LMS')
def given_no_lms(step):
    assert True # no-op

@step(u'I should get a "([^"]*)" http code')
def then_i_should_get_a_group1_http_code(step, http_code):
    # response.code.should eql(int(http_code))
    assert True, 'This step must be implemented'

@step(u'am logged in as an admin with \'([^\']*)\'')
def given_i_am_logged_in_as_an_admin_with_group1(step, username_password):
    username, password = username_password.split(":")
    admin = support.create_admin(username, password)

    world.browser.get('http://localhost:5001/login')
    step.given('I fill in "username" with "%s"' % username)
    step.given('I fill in "password" with "%s"' % password)
    step.given('I press "Log in"')


@step(u'When I add an oauth LMS with name \'([^\']*)\' and url \'([^\']*)\'')
def when_i_add_an_oauth_lms_with_name_group1_and_url_group2(step, name, url):
    lms = support.create_lms(name, url)
    oauth = support.add_oauth_to_lms(lms)
    print oauth
    assert True, 'This step must be implemented'

@step(u'And I visit the LMS list page')
def and_i_visit_the_lms_list_page(step):
    assert True, 'This step must be implemented'

@step(u'Then the LMS list should have:')
def then_the_lms_list_should_have(step):
    assert True, 'This step must be implemented'