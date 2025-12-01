from jsweb import (
    Form,
    StringField,
    PasswordField,
    FileField,
    DataRequired,
    Email,
    Length,
    EqualTo,
    FileRequired,
    FileAllowed,
    FileSize
)

class RegistrationForm(Form):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=25)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField(
        'Confirm Password',
        validators=[DataRequired(), EqualTo('password', message='Passwords must match.')]
    )

class LoginForm(Form):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])

class UploadForm(Form):
    file = FileField('File', validators=[
        FileRequired(),
        FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'pdf', 'txt']),
        FileSize(max_size=5 * 1024 * 1024)  # 5MB max
    ])