#
# Flask configuration
# 

DEBUG      = True
SECRET_KEY = 'secret'

# 
# DB Configuration
# 
USERNAME = 'labmanager'
PASSWORD = 'labmanager'
HOST     = 'localhost'
DBNAME   = 'labmanager'

SQLALCHEMY_ENGINE_STR = "mysql://%s:%s@%s/%s" % (USERNAME, PASSWORD, HOST, DBNAME)
USE_PYMYSQL = True

