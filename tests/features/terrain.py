# -*- coding: utf-8 -*-
import os
from lettuce import Runner, registry, before, after, world
from splinter import Browser
from pyvirtualdisplay import Display
from selenium import webdriver

os.environ['LAB_ENV'] = os.environ.get('LAB_ENV', 'test')
os.environ['PORT']    = os.environ.get('PORT', '5001')

import labmanager
from labmanager.database import db_session, init_db

@before.all
def load_application():
    """Load the Lab Manager application using flask's test client"""
    world.display = Display(visible=0, size=(800, 600))
    world.display.start()
    world.db_session = db_session
    world.labmanager = labmanager
    world.app = labmanager.app
    world.app.config['TESTING'] = True
    world.app.config['CSRF_ENABLED'] = False
    world.labmanager.bootstrap()
    world.browser = webdriver.Firefox()

@before.each_scenario
def reset_database(scenario):
    db_session.remove()
    init_db(drop = True)

@after.all
def tear_down_app(app):
    world.browser.quit()
    world.display.stop()
    db_session.remove()
    init_db(drop = True)