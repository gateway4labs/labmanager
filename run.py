# -*-*- encoding: utf-8 -*-*-
# 
# lms4labs is free software: you can redistribute it and/or modify
# it under the terms of the BSD 2-Clause License
# lms4labs is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

"""
  :copyright: 2012 Pablo Orduña, Elio San Cristobal, Alberto Pesquera Martín
  :license: BSD, see LICENSE for more details
"""


import os
import sys

if os.path.exists("env/bin"):
    activate_this = 'env/bin/activate_this.py'
elif os.path.exists(r"env\Scripts"):
    activate_this = r'env\Scripts\activate_this.py'
else:
    print >> sys.stderr, "Error: env not found"
    sys.exit(-1)
    
execfile(activate_this, dict(__file__=activate_this))

from labmanager.server import run

if __name__ == '__main__':
    run()

