from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Log In')

class SignUpForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Sign Up')

class SubmissionForm(FlaskForm):
    source = StringField('Source', validators=[DataRequired()])
    body = TextAreaField('Body', validators=[DataRequired(), Length(max=500)])
    username = StringField('Username', validators=[DataRequired()])
    status = SelectField('Status', choices=[('approved', 'Approved'), ('rejected', 'Rejected'), ('pending', 'Pending')], validators=[DataRequired()])
    quote_or_fact = SelectField('Quote or Fact', choices=[('quote', 'Quote'), ('fact', 'Fact')], validators=[DataRequired()])
    source_type = SelectField('Source Type', choices=[('movie', 'Movie'), ('tv', 'TV'), ('book', 'Book'), ('game', 'Game')], validators=[DataRequired()])
    submit = SubmitField('Submit')
    