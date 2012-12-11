# -*-*- encoding: utf-8 -*-*-
# 
# lms4labs is free software: you can redistribute it and/or modify
# it under the terms of the BSD 2-Clause License
# lms4labs is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

"""
In order to implement a RLMS plug-in, the following steps are required:

 1. Implement a BaseRLMS-based class, which is essentially a RLMS client.
    This class must be called RLMS.

 2. Implement a BaseFormCreator-based class, which provides the WTForms
    required to store, serialize and validate the RLMS dependent fields.
    There must be an instance of this class at module level called
    FORM_CREATOR.

"""


from abc import ABCMeta, abstractmethod

class BaseRLMS(object):
    """
    BaseRLMS is the abstract class which defines the interface 
    of every RLMS implementation. The constructor will receive a 
    single 'configuration' argument, which is the RLMS dependent
    configuration, serialized as JSON.
    """

    __metaclass__ = ABCMeta

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
    def reserve(self, laboratory_id, username, general_configuration_str, particular_configurations, request_payload, user_agent, origin_ip, referer):
        """reserve(laboratory_id, username, general_configuration_str, particular_configurations, request_payload, user_agent, origin_ip, referer) -> URL 

        reserve will request a new reservation for a username called `username` to a laboratory 
        identified by `laboratory_id`. This identifier was provided by the get_laboratories() method.

        Each LMS will have a general configuration. This configuration depends on the particular RLMS.
        For example: the WebLab-Deusto RLMS will define a 'time' and a 'priority' fields. Even if the
        RLMS grants 3600 seconds for one laboratory, the LabManager administrator may have defined
        that lms1 has maximum only 1800 seconds. These restrictions are provided with the JSON-encoded
        general_configuration_str.

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

        Additional arguments are passed, which may be useful for the RLMS developer (such as
        user_agent, origin_ip, or referer).

        Finally, the request_payload argument is a dictionary with the whole request. In particular, 
        it contains a field called 'initial' which is the information submitted by the SCORM object. 
        For instance, if there is a certain initialization argument, it can be passed through this
        field.

        This method should return an independent URL where the LMS can redirect the user to and 
        complete the reservation.
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

