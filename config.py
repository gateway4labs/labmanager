import os
import yaml

LAB_ENV = os.environ.get('LAB_ENV', 'development')
env_config = yaml.load(open('labmanager/config/database.yml'))[LAB_ENV]

# Have you run... "pip install git+https://github.com/lms4labs/rlms_weblabdeusto.git" first?
RLMS = ['weblabdeusto','unr']

SQLALCHEMY_ENGINE_STR = os.environ.get('DATABASE_URL', None)
USE_PYMYSQL = env_config.get('pymsql', False)

if SQLALCHEMY_ENGINE_STR is None:
    if env_config['engine'] == 'mysql':
        SQLALCHEMY_ENGINE_STR = "mysql://%s:%s@%s/%s" % \
            (env_config['username'], env_config['password'],
            env_config['host'], env_config['dbname'])

    elif env_config['engine'] == 'sqlite':
        SQLALCHEMY_ENGINE_STR = "sqlite:///%s.db" % env_config['dbname']
    elif env_config['engine'] == 'postgres':
        SQLALCHEMY_ENGINE_STR = "postgresql+%s://%s:%s@%s/%s" % \
            (env_config['driver'], env_config['username'],
            env_config['password'], env_config['host'], env_config['dbname'])
    elif env_config['engine'] == 'oracle':
        SQLALCHEMY_ENGINE_STR = "oracle://%s:%S@%s/%s" % \
        (env_config['username'], env_config['password'], env_config['host']
        , env_config['dbname'])


print SQLALCHEMY_ENGINE_STR
#
# Flask configuration
# 

DEBUG      = True
SECRET_KEY = 'secret'
DEBUGGING_REQUESTS = False

# 
# heroku = os.environ.get('HEROKU', None)
# testing = os.environ.get('TESTING_LABMANAGER', None)
# if heroku:
#     SQLALCHEMY_ENGINE_STR = os.environ.get('DATABASE_URL')
#     USE_PYMYSQL = False
# elif testing:
#     SQLALCHEMY_ENGINE_STR = os.environ['TESTING_LABMANAGER']
#     USE_PYMYSQL = False
# else:
# 
#     # 
#     # DB Configuration
#     # 
#     USERNAME = 'labmanager'
#     PASSWORD = 'labmanager'
#     HOST     = 'localhost'
#     DBNAME   = 'labmanager'
# 
#     ENGINE   = 'mysql' # or 'sqlite', 'postgresql', 'oracle'
#     USE_PYMYSQL = False
# 
#     