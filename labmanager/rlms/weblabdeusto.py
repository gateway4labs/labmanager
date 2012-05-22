import json

from flaskext.wtf import Form, TextField, PasswordField, Required, URL, ValidationError

from labmanager.forms import AddForm


class AddForm(AddForm):
    remote_login = TextField("Login",        validators = [Required()])
    password     = PasswordField("Password", validators = [Required()])

    login_url    = TextField("Login URL",    validators = [Required(), URL() ])
    core_url     = TextField("Core URL",     validators = [Required(), URL() ])

    mappings     = TextField("Mappings",     default = "{}")

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

