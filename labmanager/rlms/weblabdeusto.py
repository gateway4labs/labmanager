import json

from flaskext.wtf import Form, TextField, PasswordField, Required, IntegerField, URL, ValidationError

from labmanager.forms import AddForm, RetrospectiveForm
from labmanager.data import Laboratory

from .weblabdeusto_client import WebLabDeustoClient

class AddForm(AddForm):

    remote_login = TextField("Login",        validators = [Required()])
    password     = PasswordField("Password")

    base_url     = TextField("Base URL",    validators = [Required(), URL() ])

    mappings     = TextField("Mappings",     validators = [Required()], default = "{}")

    def __init__(self, add_or_edit, *args, **kwargs):
        super(AddForm, self).__init__(*args, **kwargs)
        self.add_or_edit = add_or_edit

    @staticmethod
    def process_configuration(old_configuration, new_configuration):
        old_configuration_dict = json.loads(old_configuration)
        new_configuration_dict = json.loads(new_configuration)
        if new_configuration_dict.get('password', '') == '':
            new_configuration_dict['password'] = old_configuration_dict.get('password','')
        return json.dumps(new_configuration_dict)

    def validate_password(form, field):
        if form.add_or_edit and field.data == '':
            raise ValidationError("This field is required.")

    def validate_mappings(form, field):
        try:
            content = json.loads(field.data)
        except:
            raise ValidationError("Invalid json content")
        
        if not isinstance(content, dict):
            raise ValidationError("Dictionary expected")
        
        for key in content:
            if not isinstance(key, basestring):
                raise ValidationError("Keys must be strings")
           
            if '@' not in key:
                raise ValidationError("Key format: experiment_name@experiment_category ")
                
            value = content[key]
            if not isinstance(value, basestring):
                raise ValidationError("Values must be strings")
           
            if '@' not in value:
                raise ValidationError("Value format: experiment_name@experiment_category ")

class PermissionForm(RetrospectiveForm):
    priority = TextField("Priority")
    time     = TextField("Time (in seconds)")

    def validate_number(form, field):
        if field.data != '' and field.data is not None:
            try:
                int(field.data)
            except:
                raise ValidationError("Invalid value. Must be an integer.")


    validate_priority = validate_number
    validate_time     = validate_number

def connection_tester(configuration):
    config = json.loads(configuration)
    return None

class ManagerClass(object):
    def __init__(self, configuration):
        config = json.loads(configuration or '{}')
        self.login    = config.get('remote_login')
        self.password = config.get('password')
        self.base_url = config.get('base_url')
        
        if self.login is None or self.password is None or self.base_url is None:
            raise Exception("Laboratory misconfigured: fields missing" )

    def get_laboratories(self):
        client = WebLabDeustoClient(self.base_url)
        session_id = client.login(self.login, self.password)
        experiments = client.list_experiments(session_id)
        laboratories = []
        for experiment in experiments:
            id = '%s@%s' % (experiment['experiment']['name'], experiment['experiment']['category']['name'])
            laboratories.append(Laboratory(id, id))
        return laboratories

