from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField
from wtforms.validators import DataRequired
from wtforms_components import ColorField

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Sign In')

class CreatePlaylistForm(FlaskForm):
    title = StringField('Title of the playlist', validators=[DataRequired()])
    descr = TextAreaField('Description (optional):')
    color = ColorField('Background color: ', id="playlist_color")
    privacy = PasswordField('Playlist password (optional):')
    submit = SubmitField('Create')
