import re
import sys
import time
import subprocess

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException

from labmanager.sample_data import add_sample_users

CURRENT_PORT=5001

class IntegrationTestCase(object):
    """
    This class wraps Selenium. So the setUp method
    will rebuild the database, create a client and the
    selenium driver. Subclasses can focus on creating
    the proper tests. It also provides two utility
    methods: is_element_present, is_alert_present and
    close_alert_and_get_its_text.

    Important note: this class does not inherit from
    unittest.TestCase. Subclasses must inherit from
    both this class and unittest.TestCase. This is done
    this way so test discoverers do not find this class
    and try to execute it.

    Creating new tests is as simple as running Firefox
    with selenium and running the whole process.
    """

    def setUp(self):
        # setup gateway4labs environment
        add_sample_users()
        
        global CURRENT_PORT
        CURRENT_PORT += 1

        print "Launching process..."
        self.flask_process = subprocess.Popen([sys.executable, 'run.py', '--port', str(CURRENT_PORT), '--register-fake-rlms', '--testing'])
        print "Launched"

        # setup selenium environment
        self.driver = webdriver.Firefox()
        self.driver.implicitly_wait(30)
        self.base_url = "http://localhost:%s/" % CURRENT_PORT
        self.verificationErrors = []
        self.accept_next_alert = True

        print "Base URL: ", self.base_url

    def tearDown(self):
        try:
            self.driver.quit()
            self.assertEqual([], self.verificationErrors)
        finally:
            try:
                self.flask_process.terminate()
                self.flask_process.kill()
            except OSError: # Already killed
                print "Error killing"
            
            self.flask_process.wait()

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

