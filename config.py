import os

#
# Flask configuration
#

DEBUG      = True
SECRET_KEY = 'secret'
DEBUGGING_REQUESTS = False

SQLALCHEMY_ENGINE_STR = os.environ.get('DATABASE_URL')
