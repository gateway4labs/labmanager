# -*- coding: utf-8 -*-

from lettuce import Runner, registry, before, after, world
from splinter import Browser
from pyvirtualdisplay import Display
from selenium import webdriver


import labmanager

@before.all
def load_application():
    """Load the Lab Manager application using flask's test client"""

    world.labmanager = labmanager
    world.labmanager.app.config['TESTING'] = True
    world.labmanager.app.config['CSRF_ENABLED'] = False
    world.client = labmanager.test_client()

    display = Display(visible=1, size=(800, 600))
    display.start()
    browser = webdriver.Firefox()
    browser.get('http://localhost:5000')
    print browser.title

@after.all
def tear_down_app():
    browser.quit()
    display.stop()    