# -*- coding: utf-8 -*-
from lettuce import step, world
from lettuce_webdriver import webdriver

import .steps.authentication
import support

@step(u'I add an oauth LMS with name "([^"]*)" and url "([^"]*)"')
def when_i_add_an_oauth_lms_with_name_group1_and_url_group2(step, name, url):
    support.fill_in_lms_fields(step, name, url)
    step.given('I press "Submit"')

@step(u'I visit the LMS list page')
def and_i_visit_the_lms_list_page(step):
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
