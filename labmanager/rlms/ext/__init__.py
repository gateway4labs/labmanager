# -*-*- encoding: utf-8 -*-*-
# 
# gateway4labs is free software: you can redistribute it and/or modify
# it under the terms of the BSD 2-Clause License
# gateway4labs is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

"""
Support external plug-ins without dealing with package or directory problems.
Doing:

  from labmanager.rlms.ext.weblabdeusto import foo

Will internally do:

  from g4l_rlms_weblabdeusto import foo

We use the flask.exthook to do this.
"""

def setup():
    from flask.exthook import ExtensionImporter
    importer = ExtensionImporter(['g4l_rlms_%s'], __name__)
    importer.install()


setup()
del setup
