import os
import sys

def data_filename(fname):
    basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    if os.path.exists(os.path.join(basedir, 'labmanager_data', fname)):
        return os.path.join(basedir, 'labmanager_data', fname)
    if os.path.exists(os.path.join(sys.prefix, 'labmanager_data', fname)):
        return os.path.join(sys.prefix, 'labmanager_data', fname)
    elif os.path.exists(os.path.join(basedir, fname)):
        return os.path.abspath(os.path.join(basedir, fname))
    else:
        return fname
