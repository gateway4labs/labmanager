import urllib2
import json
import getpass

config_file = raw_input("Give me configuration file (or press enter to interactively ask for data): ")
if config_file == '':
    base_url  = raw_input("Give me base URL (e.g. http://localhost:5000/): ")
    user      = raw_input("Give me the LMS username: ")
    password  = getpass.getpass("Give me the LMS password: ")
    course    = raw_input("Give me the course: ")
    lab       = raw_input("Give me the lab identifier: ")
else:
    execfile(config_file)

payload = {
    'action'     : 'reserve',
    'experiment' : lab,
}

request_data = {
   "user-id"    : "jsmith",
   "full-name"  : "John Smith",
   "is-admin"   : True,
   "user-agent" : "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:12.0) Gecko/20100101 Firefox/12.0",
   "origin-ip"  : "192.168.1.1",
   "referer"    : "http://.../",
   "courses"    : {
       course   : "s",
   },
   "request-payload" : json.dumps(payload)
}

url = base_url + '/gateway4labs/labmanager/requests/'
req = urllib2.Request(url, '')
req.add_header('Content-type','application/json')

password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
password_mgr.add_password(None, base_url, user, password)
password_handler = urllib2.HTTPBasicAuthHandler(password_mgr)
opener = urllib2.build_opener(password_handler)

print opener.open(req, json.dumps(request_data)).read()
