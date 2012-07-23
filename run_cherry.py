from cherrypy import wsgiserver
from labmanager.server import app

# TODO: http://docs.cherrypy.org/dev/refman/process/plugins/signalhandler.html

server = wsgiserver.CherryPyWSGIServer(('0.0.0.0', 8070), app)

server.start()
