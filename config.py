import os

#
# Flask configuration
# 

DEBUG      = True
SECRET_KEY = 'secret'
DEBUGGING_REQUESTS = False


heroku = os.environ.get('HEROKU', None)
if heroku:
    SQLALCHEMY_ENGINE_STR = os.environ.get('DATABASE_URL')
else:
    
    # 
    # DB Configuration
    # 
    USERNAME = 'labmanager'
    PASSWORD = 'labmanager'
    HOST     = 'localhost'
    DBNAME   = 'labmanager'
    
    ENGINE   = 'mysql' # or 'sqlite', 'postgresql', 'oracle'
    
    if ENGINE == 'mysql':
        SQLALCHEMY_ENGINE_STR = "mysql://%s:%s@%s/%s" % (USERNAME, PASSWORD, HOST, DBNAME)
        USE_PYMYSQL = True # or False, if MySQLdb is provided
    elif ENGINE == 'sqlite':
        SQLALCHEMY_ENGINE_STR = "sqlite:///%s.db" % DBNAME
    elif ENGINE == 'postgres':
        DRIVER = 'pg8000' # or 'psycopg2'
        SQLALCHEMY_ENGINE_STR = "postgresql+%s://%s:%s@%s/%s" % (DRIVER, USERNAME, PASSWORD, HOST, DBNAME)
    elif ENGINE == 'oracle':
        SQLALCHEMY_ENGINE_STR = "oracle://%s:%S@%s/%s" % (USERNAME, PASSWORD, HOST, DBNAME)

  # 
  # Not required: if you need to use a different domain name for external users
  # add this variable:
  # 
  # URL_ROOT = "http://my-domain:5000/"
  # 
