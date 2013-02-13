# -*- coding: utf-8 -*-
import os
from lettuce import Runner, registry, before, after, world
from splinter import Browser
from pyvirtualdisplay import Display
from selenium import webdriver

os.environ['LAB_ENV'] = os.environ.get('LAB_ENV', 'test')
os.environ['PORT'] = os.environ.get('PORT', '5001')

import labmanager

@before.all
def load_application():
    """Load the Lab Manager application using flask's test client"""
    world.display = Display(visible=0, size=(800, 600))
    world.display.start()
    world.labmanager = labmanager
    world.labmanager.app.config['TESTING'] = True
    world.labmanager.app.config['CSRF_ENABLED'] = False
    world.labmanager.bootstrap()
    world.client = labmanager.app.test_client()
    world.browser = webdriver.Firefox()

@after.all
def tear_down_app(app):
    world.browser.quit()
    world.display.stop()