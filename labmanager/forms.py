from flaskext.wtf import Form, TextField, Required


class MyForm(Form):
    name = TextField(name, validators=[Required()])


