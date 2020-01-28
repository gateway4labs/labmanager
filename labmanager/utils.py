import os
import sys
import ipaddress

from flask import request
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

def remote_addr():
    if not request.headers.getlist("X-Forwarded-For"):
        return request.remote_addr

    return request.headers.getlist("X-Forwarded-For")[0]

def anonymize_ip_address(ip_address):
    if not ip_address:
        return ip_address

    potential_ip_addresses = []

    for potential_ip_address in ip_address.split(','):
        potential_ip_address = potential_ip_address.strip()
        if not isinstance(potential_ip_address, unicode):
            potential_ip_address = potential_ip_address.decode()

        try:
            complete_ip_address = ipaddress.ip_address(potential_ip_address)
        except:
            # Error parsing potential_origin
            continue

        # Remove 80 bits or 8 bits, depending on the version
        if complete_ip_address.version == 6:
            bytes_removed = 10
        elif complete_ip_address.version == 4:
            bytes_removed = 1
        else:
            raise Exception("IP version {} not supported: {}".format(complete_ip_address.version, potential_ip_address))

        anonymized_packed = complete_ip_address.packed[:-bytes_removed] + (b'\x00' * bytes_removed)
        anonymized_ip_address = ipaddress.ip_address(anonymized_packed)
        potential_ip_addresses.append(anonymized_ip_address.compressed)

    return ', '.join(potential_ip_addresses)
        

class FullyQuotedUrlConverter(PathConverter):
    def to_python(self, value):
        return url_unquote(url_unquote(url_unquote(value)))

    def to_url(self, value):
        return url_quote(url_quote(url_quote(value, self.map.charset, safe=''), self.map.charset, safe=''), self.map.charset, safe='')

class EverythingConverter(PathConverter):
    regex = '.*?'

