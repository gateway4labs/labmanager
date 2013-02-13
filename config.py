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

#
# Flask configuration
# 

DEBUG      = True
SECRET_KEY = 'secret'
DEBUGGING_REQUESTS = False
