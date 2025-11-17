from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField, FloatField, SelectField, DateField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional
from flask_wtf.file import FileField, FileAllowed

class LoginForm(FlaskForm):
    """Form for manager login."""
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Login')

class EmployeeForm(FlaskForm):
    """Form to Add/Edit an Employee."""
    name = StringField('Full Name', validators=[DataRequired()])
    employee_login = StringField('Employee Login', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    photo = FileField('Profile Photo', validators=[FileAllowed(['jpg', 'png', 'jpeg'], 'Images only!')])
    submit = SubmitField('Save Employee')

class ProjectForm(FlaskForm):
    """Form to Add/Edit a Project."""
    title = StringField('Project Title', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[Optional()])
    actions_taken = TextAreaField('Actions Taken', validators=[Optional()])
    solution = TextAreaField('Solution', validators=[Optional()])
    impact_usd = FloatField('Impact in $', validators=[Optional()])
    stakeholder_login = StringField('Stakeholder Login', validators=[Optional()])
    status = SelectField('Status', choices=[('In Progress', 'In Progress'), ('Completed', 'Completed')], validators=[DataRequired()])
    submit = SubmitField('Save Project')

class AttendanceForm(FlaskForm):
    """Form to add a leave day."""
    date = DateField('Date', format='%Y-%m-%d', validators=[DataRequired()])
    leave_type = SelectField('Leave Type', choices=[
        ('Annual', 'Annual Leave'),
        ('Casual', 'Casual Leave'),
        ('Sick', 'Sick Leave'),
        ('Maternity', 'Maternity Leave')
        # 'Present' is the default, so we only log exceptions
    ], validators=[DataRequired()])
    submit = SubmitField('Add Leave')