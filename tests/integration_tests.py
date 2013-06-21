import time
import re
import os
import sys
import subprocess

if __name__ == '__main__':
    os.environ['LAB_ENV'] = os.environ.get('LAB_ENV', 'test')
    os.environ['PORT']    = os.environ.get('PORT', '5001')
    
    server_process = subprocess.Popen("%s run.py" % sys.executable, shell = True)
    # time.sleep(1)
    try:
        os.system("python labmanager/test/test_lms.py")
        os.system('lettuce tests/features')
    finally:
        server_process.kill()
        server_process.wait()
