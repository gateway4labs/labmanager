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

