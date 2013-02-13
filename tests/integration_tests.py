from __future__ import with_statement
import time
import re
from fabric import api

def run_services():
    api.local("python run.py > /dev/null 2>&1 &")

def kill_services():
    """
    brutally kill off any existing processes
    """
    kill_flask()

def kill_flask():
    process = find_flask().split()
    if len(process) > 0:
        pid = process[0]
        api.local("kill " + pid)

def find_flask():
    return api.local('ps ax |grep "bin/python run.py" |grep -v grep', capture=True)

def psaxf_report(capture = False):
    """
    give me a dump of the processes running...
    """
    return api.local('ps ax |grep python |grep -v grep', capture=capture)

if __name__ == '__main__':
    with api.settings(warn_only=True):
        kill_services()

    with api.settings(warn_only=False):
        run_services()
    # time.sleep(1)
    psaxf_report()
    api.local("python labmanager/test/test_lms.py")
    api.local('lettuce tests/features --verbosity=2')
    kill_services()