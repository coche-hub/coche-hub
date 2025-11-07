from flask_wtf import FlaskForm
from wtforms import BooleanField, PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, Length, Regexp


class SignupForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired(), Length(max=100)])
    surname = StringField("Surname", validators=[DataRequired(), Length(max=100)])
    password = PasswordField("Password", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired(), Email()])
    submit = SubmitField("Submit")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember_me = BooleanField("Remember me")
    submit = SubmitField("Login")


class Email2FAVerificationForm(FlaskForm):
    code = StringField(
        "Validation code",
        validators=[
            DataRequired(),
            Length(min=6, max=6, message="Code must be exactly 6 digits"),
            Regexp(r"^\d{6}$", message="Code must contain only digits"),
        ],
    )
    submit = SubmitField("Verify")
