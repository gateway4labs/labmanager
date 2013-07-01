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

    WIDGET        = 'widget'
    """
    Providing this capability reports that the RLMS plug-in supports
    that the UI is splitted. This is useful for its inclusion in 
    widgets (e.g., in the Graasp OpenSocial widgets).
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

    @abstractmethod
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
    def reserve(self, laboratory_id, username, general_configuration_str, particular_configurations, request_payload, user_properties, *args, **kwargs):
        """reserve(laboratory_id, username, general_configuration_str, particular_configurations, request_payload, user_agent, origin_ip, referer) -> {}

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

    def load_widget(self, reservation_id, widget_name):
        """
        This method is optional. It will only be called if the capability Capabilities.WIDGET is reported
        in the method "get_capabilities()".

        If the RLMS plug-in supports widget, this method will return a
        dictionary with a proper URL for loading a widget. At this point, the dictionary only contains:

         - 'url' : '(where to load the widget)

        But in the future it might contain other fields (such as the width of the field or so on).
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

    __metaclass__ = ABCMeta

    @abstractmethod
    def get_add_form(self):
        """get_add_form() -> AddForm

        Returns a RLMS dependent WTForm class, which inherits from labmanager.forms.AddForm.
        The purpose of this class is to request RLMS specific parameters, validate them, and
        generate a RLMS dependent JSON file.
        """

    @abstractmethod
    def get_permission_form(self):
        """get_permission_form() -> PermissionForm

        Returns a RLMS dependent form for managing course-level permissions.
        """

    @abstractmethod
    def get_lms_permission_form(self):
        """get_lms_permission_form() -> LmsPermissionForm
        
        Returns a RLMS dependent form for managing lms-level permissions. The main difference
        with get_permission_form is that they must have an identifier, so it should inherit from
        labmanager.forms.GenericPermissionForm.
        """

_BLUEPRINTS = {
    # url : blueprint
}

def register_blueprint(blueprint, url):
    if url in _BLUEPRINTS:
        raise Exception("Attempt to register %r for url %r, but %r was already registered for that URL" % (_BLUEPRINTS[blueprint], url, blueprint))

    _BLUEPRINTS[url] = blueprint

