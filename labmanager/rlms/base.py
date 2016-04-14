# -*-*- encoding: utf-8 -*-*-
# 
# gateway4labs is free software: you can redistribute it and/or modify
# it under the terms of the BSD 2-Clause License
# gateway4labs is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

"""
A RLMS plug-in is composed of a module or package, called g4l_rlms_FOO, which
will have a function called get_module(version):

   def get_module(version):
       # ...
       return # the plug-in module for that version

This way, with get_module a single plug-in may support different versions. An
example of an strict version parser would be the following:

   def get_module(version):
       if version.startswith( ('4.', '5.') ):
          import mylab4
          return mylab4
       elif version.startswith('6.'):
          import mylab6
          return mylab6
       else:
          raise ValueError("Version not supported by XXX plug-in: %s" % version)

Although most times, the implementation will simply return the current module, such as:

   def get_module(version):
       return sys.modules[__name__]

The returned module by get_module must have two variables defined, called RLMS
and FORM_CREATOR. So as to do it:

 1. Implement a BaseRLMS-based class, which is essentially a RLMS client.
    This class must be called RLMS.

 2. Implement a BaseFormCreator-based class, which provides the WTForms
    required to store, serialize and validate the RLMS dependent fields.
    There must be an instance of this class at module level called
    FORM_CREATOR.

Finally, the module must call the labmanager.rlms.register() function providing
itself.

So as to develop the RLMS class, the RLMS plug-in can create a Flask blueprint and 
register it. In the case of a plug-in called "foo", it would be:

    from flask import Blueprint
    from labmanager.rlms import register_blueprint

    foo_blueprint = Blueprint('foo', __name__)

    @foo_blueprint.route("/")
    def index():
        return "Hi, this is the index. It will be located in /labmanager/rlms/foo/"

    @foo_blueprint.route("/calendar")
    def calendar():
        return "Here you can use all the Flask system"

    register_blueprint(FOO_blueprint, '/foo/')

The RLMS may also need to access the RLMS.

"""

from abc import ABCMeta, abstractmethod
from flask import Blueprint
assert Blueprint or None # Avoid pyflakes warning
from labmanager.forms import AddForm, RetrospectiveForm, GenericPermissionForm

# 
# This is the list of versions. The BaseRLMS has a method
# "get_version()", which will return one of these messages.
# The rest of the labmanager interacts with it, and will 
# call the proper methods using the appropriate formats for
# those versions. 
#
class Versions(object):
    VERSION_1 = "version1"

class Capabilities(object):
    """ 
    Capabilities: a RLMS may support only a subset of capabilities.
    For instance, it may implement a layer for showing the results
    to the teacher, or it may not. It may support that the user 
    interface is splitted or not.
    """

    TEACHER_PANEL = 'teacher_panel'
    """
    Providing this capability shows that the RLMS plug-in has 
    implemented a user interface so teachers can see something else 
    (such as what their students did or so).
    """

    WIDGET = 'widget'
    """
    Providing this capability reports that the RLMS plug-in supports
    that the UI is splitted. This is useful for its inclusion in 
    widgets (e.g., in the Graasp OpenSocial widgets).
    """

    FORCE_SEARCH = 'force_search'
    """
    Providing this capability reports that the RLMS plug-in does not 
    list laboratories automatically. It forces the user to make a query
    to provide labs. The Labmanager will report this to the user.
    """

    TRANSLATIONS = 'translations'
    """
    Providing this capability reports that the RLMS plug-in supports
    a method called 'get_translations', which will return a dictionary of 
    translations per laboratory.
    """

    TRANSLATION_LIST = 'translation_list'
    """
    Providing this capability reports that the RLMS plug-in supports
    a method called 'get_translation_list', which will return a list of
    ISO 639-1 messages detailing what languages are supported by the server
    side. If TRANSLATIONS is provided this method is not required.
    """


    LOGGING_URL = 'logging_url'
    """
    Providing this capability reports that the RLMS plug-in supports
    a method called 'get_logging_url', which will return a URL to obtain
    a set of data usage in Activity Streams format.
    """

class BaseRLMS(object):
    """
    BaseRLMS is the abstract class which defines the interface 
    of every RLMS implementation. The constructor will receive a 
    single 'configuration' argument, which is the RLMS dependent
    configuration, serialized as JSON.
    """

    __metaclass__ = ABCMeta

    @abstractmethod
    def get_version(self):
        """get_version()

        Version supported by this RLMS. At this moment, there is a single
        version, called "VERSION_1"
        """

    @abstractmethod
    def get_capabilities():
        """get_capabilities() -> [ Capability1, Capability2 ]

        Provides the set of capabilities supported by this plug-in.
        For example:

            return [ Capabilities.WIDGET, Capabilities.TEACHER_PANEL ]

        """

    # Not required.
    # @abstractmethod
    def test(self):
        """test()
        
        test will test if the current configuration is valid or not (valid URLs, valid credentials, 
        etc.) by connecting to the foreign server.
        """

    @abstractmethod
    def get_laboratories(self):
        """get_laboratories() -> [ Laboratory(name, identifier), Laboratory(name1, identifier2) ]

        get_laboratories will query this RLMS instance to retrieve the laboratories that are
        available with the configured credentials. These credentials were passed to this instance
        through the JSON configuration str in the constructor.
        """

    @abstractmethod
    def reserve(self, laboratory_id, username, institution, general_configuration_str, particular_configurations, request_payload, user_properties, *args, **kwargs):
        """reserve(laboratory_id, username, institution, general_configuration_str, particular_configurations, request_payload, user_properties ) -> {}

        reserve will request a new reservation for a username called `username` to a laboratory 
        identified by `laboratory_id`. This identifier was provided by the get_laboratories() method.

        Each LMS/CMS/PLE will have a general configuration. This configuration depends on the 
        particular RLMS.  For example: the WebLab-Deusto RLMS will define a 'time' and a 'priority' 
        fields. Even if the RLMS grants 3600 seconds for one laboratory, the LabManager administrator 
        may have defined that lms1 has maximum only 1800 seconds. These restrictions are provided with 
        the JSON-encoded general_configuration_str.

        The courses where the student is enrolled may have also different configurations each. For 
        example: in the previous case, the lms1 LMS may have 2 courses. While lms1 can use a 
        laboratory for 1800 seconds, they might want to enable course1 to use it for 300 seconds, and
        course2 to use it for 600 seconds. Depending on the LMS, it may be possible to know
        what particular course is being executed. If possible (e.g. in LTI-based systems, such as 
        Moodle >= 2.2), particular_configurations will be a list with a single list with the 
        configuration of that course. If it is not possible (e.g. in Moodle 1.x, < 2.2), 
        particular_configurations will be a list of all the configurations of those courses where
        the student is enrolled in.

        This way, it's up to the RLMS developer to submit to the RLMS a request asking for the best 
        configuration available in the particular_configurations list, as long as it's worse than the
        general_configuration_str. For example, if a user is enrolled in course1 and course2 of lms1,
        the request should ask for 600 seconds (which is the best of course1 and course2, but worse 
        than lms1).
        
        Additional arguments are passed in the form of a dictionary called user_properties. It will include keys such as:
         - full_name
         - from_ip
         - referer
         - user_agent

        Finally, the request_payload argument is a dictionary with the whole request. In particular, 
        it contains a field called 'initial' which is the information submitted by the SCORM object. 
        For instance, if there is a certain initialization argument, it can be passed through this
        field.

        This method must return a dictionary with the following data:

         - 'reservation_id' : A reservation ID (in a str format)

         - 'load_url' : An independent URL where the LMS can redirect the user to and complete the 
                        reservation.
        """

    def search(self, query, page, **kwargs):
        """
        This method is optional. If provided, it must return:

        {
            'total_results' : 50,
            'pages' : 3,
            'laboratories' : [ Laboratory( ... ), Laboratory( ... ) ]
        }
        
        Otherwise, it will be implemented by calling get_laboratories() and searching there.
        """
        tokens = query.lower().split(' ')
        
        results = []
        laboratories = self.get_laboratories()
        for lab in laboratories:
            total_lab = '%s %s %s' % (lab.name, lab.laboratory_id, lab.description or '')
            total_lab = total_lab.lower()
            valid = True
            for token in tokens:
                if token not in total_lab:
                    valid = False
                    break
            if valid:
                results.append(lab)

        return {
                'total_results' : len(results),
                'pages' : 1,
                'laboratories' : results
            }

    def get_translation_list(self, laboratory_id):
        """
        This method is optional. If provided, it must return something like:
        {
            'supported_languages' : ['en', 'fr', 'de']
        }
        """
        return {}

    def get_translations(self, laboratory_id):
        """
        This method is optional. If provided, it must return something like:

        {
            'translations' : {
                'en' : {
                    'hello' : {
                        'value' : "Hello",
                        'namespace' : 'http://something'
                    },
                    'bye' : {
                        'value' : "Bye"
                    }
                },
                'es' : {
                    'hello' : {
                        'value' : "Hola",
                        'namespace' : 'http://something'
                    },
                    'bye' : {
                        'value' : "Adios"
                    }
                }
            },
            'mails' : [ 'someone@domain.com', 'somenelse@domain.com' ]
        }

        The result is that in the OpenSocial version it will display those translations.
        They will not be used, but external tools such as the App Composer will use it
        to translate those texts in an non-automatic mode. The App Composer will notify
        the people listed in 'mails' about new translations.
        """
        return {}

    def load_widget(self, reservation_id, widget_name):
        """
        This method is optional. It will only be called if the capability Capabilities.WIDGET is reported
        in the method "get_capabilities()".

        If the RLMS plug-in supports widget, this method will return a
        dictionary with a proper URL for loading a widget. At this point, the dictionary only contains:

         - 'url' : '(where to load the widget)

        But in the future it might contain other fields (such as the width of the field or so on).
        """

    def list_widgets(self, laboratory_id):
        """
        This method is optional. Only called if the Capabilities.WIDGET is provided.
        
        Given a laboratory_id, request which widgets are provided by this laboratory. Example: if 
        requested an aquarium laboratory, it may return a list like:
        [
            {
                'name' : 'camera1',
                'description' : "The camera1 shows the upper camera"
            },
            {
                'name' : 'red-ball',
                'description' : "The red ball enables you to modify the red ball"
            }
        ]
        """

    # TODO:
    # - retrieve_data() or similar
    # - user_agent, origin_ip, referer... should be a dictionary 
    #   (so if in the future we add more field, we don't need to change the interface)
    # 

class BaseFormCreator(object):
    """Any instance of BaseFormCreator will have to return custom form classes for 
    different tasks. Each form class will be RLMS dependent, and will provide the
    custom fields required by that RLMS to work.
    """

    def get_add_form(self):
        """get_add_form() -> AddForm

        Returns a RLMS dependent WTForm class, which inherits from labmanager.forms.AddForm.
        The purpose of this class is to request RLMS specific parameters, validate them, and
        generate a RLMS dependent JSON file.
        """
        if not hasattr(self, '_add_form'):
            class NewAddForm(AddForm):
                def __init__(self, add_or_edit, *args, **kwargs):
                    super(ViSHAddForm, self).__init__(*args, **kwargs)
                    self.add_or_edit = add_or_edit
            self._add_form = NewAddForm
        return self._add_form

    def get_permission_form(self):
        """get_permission_form() -> PermissionForm

        Returns a RLMS dependent form for managing course-level permissions.
        """
        return RetrospectiveForm

    def get_lms_permission_form(self):
        """get_lms_permission_form() -> LmsPermissionForm
        
        Returns a RLMS dependent form for managing lms-level permissions. The main difference
        with get_permission_form is that they must have an identifier, so it should inherit from
        labmanager.forms.GenericPermissionForm.
        """
        if not hasattr(self, '_lms_permission_form'):
            class NewLmsPermissionForm(self.get_permission_form(), GenericPermissionForm):
                pass
            self._lms_permission_form = LmsPermissionForm
        return self._lms_permission_form
            

_BLUEPRINTS = {
    # url : blueprint
}

def register_blueprint(blueprint, url):
    if url in _BLUEPRINTS:
        raise Exception("Attempt to register %(blueprints)r for url %(url)r, but %(blueprint)r was already registered for that URL" % dict(blueprints=_BLUEPRINTS[blueprint], url=url, blueprint=blueprint))

    _BLUEPRINTS[url] = blueprint
