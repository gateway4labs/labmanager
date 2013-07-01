import urlparse
import codecs
import os
import StringIO
import zipfile

# 
# Flask imports
# 
from flask import Response, render_template, flash


def get_scorm_object(authenticate = True, laboratory_identifier = '', lms_path = '/', lms_extension = '/', html_body = '''<div id="gateway4labs_root" />\n'''):
    import labmanager
    # TODO: better way
    base_dir = os.path.dirname(labmanager.__file__)
    base_scorm_dir = os.path.join(base_dir, 'data', 'scorm')
    if not os.path.exists(base_scorm_dir):
        flash("Error: %s does not exist" % base_scorm_dir)
        return render_template("lms_admin/scorm_errors.html")

    sio = StringIO.StringIO('')
    zf = zipfile.ZipFile(sio, 'w')
    for root, dir, files in os.walk(base_scorm_dir):
        for f in files:
            file_name = os.path.join(root, f)
            arc_name  = os.path.join(root[len(base_scorm_dir)+1:], f)
            content = codecs.open(file_name, 'rb', encoding='utf-8').read()
            if f == 'lab.html' and root == base_scorm_dir:
                content = content % { 
                            u'EXPERIMENT_COMMENT'    : '//' if authenticate else '',
                            u'AUTHENTICATE_COMMENT'  : '//' if not authenticate else '',
                            u'EXPERIMENT_IDENTIFIER' : unicode(laboratory_identifier),
                            u'LMS_URL'               : unicode(lms_path),
                            u'LMS_EXTENSION'         : unicode(lms_extension),
                            u'HTML_CONTENT'          : unicode(html_body),
                        }
            zf.writestr(arc_name, content.encode('utf-8'))

    zf.close()
    return sio.getvalue()

def get_authentication_scorm(lms_url):
    lms_path = urlparse.urlparse(lms_url).path or '/'
    extension = '/'
    if 'gateway4labs/' in lms_path:
        extension = lms_path[lms_path.rfind('gateway4labs/lms/list') + len('gateway4labs/lms/list'):]
        lms_path  = lms_path[:lms_path.rfind('gateway4labs/')]

    content = get_scorm_object(True, lms_path=lms_path, lms_extension=extension)
    return Response(content, headers = {'Content-Type' : 'application/zip', 'Content-Disposition' : 'attachment; filename=authenticate_scorm.zip'})


