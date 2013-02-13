# RUNNING THE LAB MANAGER

[![Build Status](https://travis-ci.org/lms4labs/labmanager.png?branch=modular_labmanager)](https://travis-ci.org/lms4labs/labmanager)

## INSTALL

Python 2.7 is required. **Do not use Python >= 3**

`easy_install` and `pip` must be installed. `virtualenv` is also highly recommended.
First, a couple of steps which depend on the operating system:

### WINDOWS

 1. Download easy_install: http://pypi.python.org/pypi/setuptools#downloads

 1.1 Select the one that is a Windows installer
 1.2 Install it :-)

 2. Put into the PATH the following path: `C:\Python27\Scripts\` (if you're using
Python 2.7).

 3. `easy_install pip`
 4. `pip install virtualenv`
 5. `virtualenv --no-site-packages env`
 6. `env\Scripts\activate.bat`

 ### LINUX (Ubuntu)

 1. `sudo apt-get install python-pip python-setuptools python-virtualenv`

 2. `virtualenv --no-site-packages env`

 3. `. env/bin/activate`

### INSTALL

After installing the tools detailed above, you can install the missing
libraries. They will be installed in the "env" directory. Feel free to remove it
at any point.

 1. `pip install -r requirements.txt`

 2. Copy `config.py.dist` into `config.py`

 3. Edit `config.py`. By default, it uses MySQL, but you can use sqlite if you
 want. If interested in other RDBMS

 3. `python deploy.py -cdu`


Now you can run it:

`python run.py`

And see it in http://localhost:5000/


## Development

If you want to contribute to the Lab Manager application, you'll need to install
some external dependencies that are used only on development and testing.

For this, simply run:

`pip install -r requirements-test.txt`

And you're ready to go.

To test the application run:

`python labmanager/test/test_lms.py`