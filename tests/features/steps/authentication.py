from lettuce import step, world
from lettuce_webdriver import webdriver

import support

@step(u'am logged in as an admin with "([^"]*)"')
def given_i_am_logged_in_as_an_admin_with_group1(step, username_password):
    step.given('An admin user with "%s"' % username_password)
    step.given('I login with "%s"' % username_password)
    step.given('I should be logged in')

@step(u'[Aa]n? admin user with "([^"]*)"')
def given_an_admin_user_with_group1(step, username_password):
    username, password = username_password.split(":")
    support.create_admin(username, password)

@step(u'I login with "([^"]*)"')
def when_i_login_with_group1(step, username_password):
    username, password = username_password.split(":")
    world.browser.get('http://localhost:5001/login')
    step.given('I fill in "username" with "%s"' % username)
    step.given('I fill in "password" with "%s"' % password)
    step.given('I press "Log in"')

@step(u'I should be logged in')
def then_i_should_be_logged_in(step):
    # print world.browser.page_source
    step.given('I should see "You are logged in as"')
    step.given('I should see "LabManager Admin Dashboard"')

@step(u'there are no admins')
def given_there_are_no_admins(step):
    True

@step(u'I should not be logged in')
def then_i_should_not_be_logged_in(step):
    step.given('I should not see "You are logged in as"')
