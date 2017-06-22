from flask_wtf import Form
from wtforms import StringField, SubmitField, IntegerField,SelectField
from wtforms.validators import Required, Email, Length, EqualTo
from wtforms import ValidationError
from ..models import Machine

class RegistrationForm(Form):
    name = StringField('Name',validators=[Required(),Length(1,64)])
    location = StringField('Location',validators=[Required(),Length(1,64)])
    serial_no = IntegerField('Serial No', validators=[Required()])
    type = SelectField(label='Machine Type',choices=[],coerce=int, validators=[Required()])
    state = SelectField(label='Machine State',choices=[],coerce=int, validators=[Required()])
    submit = SubmitField('Register')

    def validate_name(self, field):
        if Machine.query.filter_by(name=field.data).first():
            raise ValidationError('Machine by similar name already registered')

    def validate_serial_no(self, field):
        if Machine.query.filter_by(serial_no=field.name).first():
            raise ValidationError('Serial number already registered')

class RemovalForm(Form):
    machine = SelectField(label='Selected Machine', choices=[], coerce=int, validators=[Required])
    delete = SubmitField('Delete')