# -*-*- encoding: utf-8 -*-*-
# 

from labmanager.babel import gettext

messages_codes = {
    "ERROR_enrolled" : gettext('Your LMS has permission to use that laboratory; but you are not enrolled in any course with permissions to use it'),
    "ERROR_permission" : gettext('Your LMS does not have permission to use that laboratory or that identifier does not exist'),
    "ERROR_no_good" : gettext('No good news :-('),
    "MSG_asigned" : "You have been assigned %s of type %s version %s! <br/> Try it at <a href='%s'>%s</a>",
    "ERROR_invalid_json" : gettext('Error: the request payload is not a valid JSON request'),
    "ERROR_unsupported" : gettext('Unsupported operation'),
    "ERROR_invalid" : gettext('Invalid response'),
    "ERROR_" : "ERROR: %s",
    "ERROR_json" : gettext('Could not process JSON data'),
    "ERROR_oauth_key" : gettext('The key was not recognized'),
    "ERROR_no_consumer_key" : gettext('No consumer key provided'),
    "MSG_tool_created" : gettext('Tool provider created')
    }