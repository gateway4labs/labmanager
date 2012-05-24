activate_this = 'env/bin/activate_this.py'
execfile(activate_this, dict(__file__=activate_this))

from labmanager.server import run

if __name__ == '__main__':
    run()

