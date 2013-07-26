import unittest
import time
import re

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException

class IntegrationTestCase(unittest.TestCase):
    """
    This class wraps Selenium. So the setUp method
    will rebuild the database, create a client and the
    selenium driver. Subclasses can focus on creating
    the proper tests. It also provides two utility
    methods: is_element_present, is_alert_present and
    close_alert_and_get_its_text.

    Creating new tests is as simple as running Firefox
    with selenium and running the whole process.
    """

    def setUp(self):
        # setup gateway4labs environment
        

        # setup selenium environment
        self.driver = webdriver.Firefox()
        self.driver.implicitly_wait(30)
        self.base_url = "http://localhost:5000/"
        self.verificationErrors = []
        self.accept_next_alert = True

    def is_element_present(self, how, what):
        try: self.driver.find_element(by=how, value=what)
        except NoSuchElementException, e: return False
        return True

    def is_alert_present(self):
        try: self.driver.switch_to_alert()
        except NoAlertPresentException, e: return False
        return True

    def close_alert_and_get_its_text(self):
        try:
            alert = self.driver.switch_to_alert()
            alert_text = alert.text
            if self.accept_next_alert:
                alert.accept()
            else:
                alert.dismiss()
            return alert_text
        finally: self.accept_next_alert = True

    def tearDown(self):
        self.driver.quit()
        self.assertEqual([], self.verificationErrors)

if __name__ == "__main__":
    unittest.main()
