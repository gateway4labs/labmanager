import unittest

from labmanager.tests.integration.base import IntegrationTestCase

# Utility functions. They can be used by other parts of the system

def labmanager_admin_login(testcase):
    driver = testcase.driver
    driver.get(testcase.base_url + "/")
    driver.find_element_by_link_text("Admin").click()
    driver.find_element_by_id("username").clear()
    driver.find_element_by_id("username").send_keys("admin")
    driver.find_element_by_id("password").clear()
    driver.find_element_by_id("password").send_keys("password")
    driver.find_element_by_css_selector("button.btn.btn-success").click()

def labmanager_admin_create_lms(testcase):
    labmanager_admin_login(testcase)
    driver = testcase.driver
    driver.get(testcase.base_url + "/")
    driver.find_element_by_link_text("LMS Management").click()
    driver.find_element_by_link_text("LMS").click()
    driver.find_element_by_link_text("Create").click()
    driver.find_element_by_id("name").clear()
    driver.find_element_by_id("name").send_keys("My school")
    driver.find_element_by_id("name").clear()
    driver.find_element_by_id("name").send_keys("myschool")
    driver.find_element_by_id("full_name").clear()
    driver.find_element_by_id("full_name").send_keys("My School")
    driver.find_element_by_id("url").clear()
    driver.find_element_by_id("url").send_keys("http://myschool.com/")
    driver.find_element_by_link_text("Add Basic Http Authentications").click()
    driver.find_element_by_id("basic_http_authentications-0-lms_login").clear()
    driver.find_element_by_id("basic_http_authentications-0-lms_login").send_keys("admin")
    driver.find_element_by_id("basic_http_authentications-0-lms_password").clear()
    driver.find_element_by_id("basic_http_authentications-0-lms_password").send_keys("password")
    driver.find_element_by_id("basic_http_authentications-0-lms_url").clear()
    driver.find_element_by_id("basic_http_authentications-0-lms_url").send_keys("http://localhost/foo/lms4labs/foo.php")
    driver.find_element_by_id("basic_http_authentications-0-labmanager_login").clear()
    driver.find_element_by_id("basic_http_authentications-0-labmanager_login").send_keys("admin")
    driver.find_element_by_id("basic_http_authentications-0-labmanager_password").clear()
    driver.find_element_by_id("basic_http_authentications-0-labmanager_password").send_keys("password")
    driver.find_element_by_xpath("//input[@value='Submit']").click()

class AdminIntegrationTestCase(IntegrationTestCase, unittest.TestCase):
    def test_login(self):
        labmanager_admin_login(self)
        title = self.driver.find_element_by_tag_name('h1')
        self.assertTrue('LabManager Admin Dashboard' in title.text)

    def test_create_lms(self):
        labmanager_admin_create_lms(self)
        

if __name__ == '__main__':
    unittest.main()
