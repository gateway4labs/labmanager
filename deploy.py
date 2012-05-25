activate_this = 'env/bin/activate_this.py'
execfile(activate_this, dict(__file__=activate_this))

import sys
import getpass
from optparse import OptionParser

try:
    import config
except ImportError:
    print >> sys.stderr, "Missing config.py. Copy config.py.dist into config.py"
    sys.exit(-1)

from config import USERNAME, PASSWORD, HOST, DBNAME

from config import ENGINE
if ENGINE == 'mysql':
    try:
        from config import USE_PYMYSQL
    except:
        USE_PYMYSQL = False
    if USE_PYMYSQL:
        import pymysql as dbi
    else:
        import MySQLdb as dbi
elif ENGINE == 'sqlite':
    import sqlite3 as dbi
else:
    print >> sys.stderr, "Unsupported engine %s. You will have to create the database and the users by your own." % ENGINE 

from labmanager.database import init_db, db_session, add_sample_users

ROOT_USERNAME = None
ROOT_PASSWORD = None

def create_user():
    if ENGINE == 'mysql':
        sentences = (
            "DROP USER '%s'@'localhost'" % USERNAME,
            "CREATE USER '%s'@'localhost' IDENTIFIED BY '%s'" % (USERNAME, PASSWORD),
            "GRANT ALL PRIVILEGES ON %s.* TO '%s'@'localhost' IDENTIFIED BY '%s'"  % (DBNAME, USERNAME, PASSWORD),
        )

        global ROOT_USERNAME, ROOT_PASSWORD
        ROOT_USERNAME = raw_input("MySQL administrator username (default 'root'): ") or "root"
        ROOT_PASSWORD = getpass.getpass( "MySQL administrator password: " )

        for num, sentence in enumerate(sentences):
            try:
                connection = dbi.connect(user=ROOT_USERNAME, passwd=ROOT_PASSWORD)
                cursor = connection.cursor()
                cursor.execute(sentence)
                connection.commit()
                connection.close()
            except:
                if num != 0: # If user does not exist
                    raise

def create_db():
    if ENGINE == 'mysql':
        global ROOT_USERNAME, ROOT_PASSWORD
        if ROOT_USERNAME is None or ROOT_PASSWORD is None:
            ROOT_USERNAME = raw_input("MySQL administrator username (default 'root'): ") or "root"
            ROOT_PASSWORD = getpass.getpass( "MySQL administrator password: " )

        try:
            connection = dbi.connect(user=ROOT_USERNAME, passwd=ROOT_PASSWORD, db = DBNAME, host = HOST) 
        except:
            pass # DB does not exist
        else:
            cursor = connection.cursor()
            cursor.execute("DROP DATABASE IF EXISTS %s" % DBNAME)
            connection.commit()
            connection.close()

        connection = dbi.connect(user=ROOT_USERNAME, passwd=ROOT_PASSWORD, host = HOST) 
        cursor = connection.cursor()
        cursor.execute("CREATE DATABASE %s" % DBNAME)
        connection.commit()
        connection.close()

if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option("-c", "--create-user",
                    action="store_true", dest="create_user", default=False,
                    help="Creates the user and password in the database first")
    parser.add_option("-d", "--create-db",
                    action="store_true", dest="create_db", default=False,
                    help="Creates the database")
    parser.add_option("-u", "--add-sample-users",
                    action="store_true", dest="add_sample_users", default=False,
                    help="Adds sample users")

    (options, args) = parser.parse_args()

    if options.create_user:
        create_user()

    if options.create_db:
        create_db()

    init_db()
    init_db(drop=True)

    if options.add_sample_users:
        add_sample_users()

