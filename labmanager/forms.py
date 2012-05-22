from flaskext.wtf import Form, TextField, Required

class RetrospectiveForm(Form):

    def get_field_names(self):
        field_names = []
        for field in self:
            if 'csrf' not in str(type(field)).lower():
                field_names.append(field.name)
        return field_names


class AddForm(RetrospectiveForm):
    name     = TextField("Name", validators=[Required()])
    location = TextField("Location", validators=[Required()])


