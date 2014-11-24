import os
import sys
from werkzeug.urls import url_quote, url_unquote
from werkzeug.routing import PathConverter


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


class FullyQuotedUrlConverter(PathConverter):
    def to_python(self, value):
        return url_unquote(url_unquote(url_unquote(value)))

    def to_url(self, value):
        return url_quote(url_quote(url_quote(value, self.map.charset, safe=''), self.map.charset, safe=''), self.map.charset, safe='')
