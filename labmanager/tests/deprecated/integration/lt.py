import unittest

from labmanager.tests.integration.base import IntegrationTestCase

# Utility functions.

def labmanager_lt_login(testcase, from_scratch = False):
    if from_scratch:
        labmanager_create_lt(testcase)

    driver = testcase.driver
    driver.find_element_by_link_text("Log out").click()
    driver.find_element_by_link_text("Manage LMS internals").click()
    driver.find_element_by_id("lms_select").click()
    driver.find_element_by_xpath('//a[@class="select2-choice"]').click()
    driver.find_element_by_xpath('//div[@class="select2-result-label" and child::text()="myschool"]').click()
    driver.find_element_by_id("username").clear()
    driver.find_element_by_id("username").send_keys("admin")
    driver.find_element_by_id("password").clear()
    driver.find_element_by_id("password").send_keys("password")
    driver.find_element_by_css_selector("button.btn.btn-success").click()

    title = driver.find_element_by_tag_name('h1')
    testcase.assertTrue('LMS Admin Dashboard' in title.text)

from labmanager.tests.integration.admin import labmanager_admin_create_lt

class LmsIntegrationTestCase(IntegrationTestCase, unittest.TestCase):
    def test_login_lt(self):
        labmanager_admin_create_lt(self)
        labmanager_lt_login(self)

if __name__ == '__main__':
    unittest.main()
