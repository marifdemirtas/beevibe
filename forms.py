from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField
from wtforms.validators import DataRequired
from flask_wtf.file import FileField, FileAllowed
from wtforms_components import ColorField


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Sign In')


class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('E-mail', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Register')


class CreatePlaylistForm(FlaskForm):
    title = StringField('Title of the playlist', validators=[DataRequired()])
    descr = TextAreaField('Description (optional):')
    color = ColorField('Background color: ', id="playlist_color")
    privacy = PasswordField('Playlist password (optional):')
    submit = SubmitField('Create')


class EditPlaylistForm(FlaskForm):
    descr = TextAreaField('Description:')
    color = ColorField('Background color: ', id="playlist_color")
    submit = SubmitField('Update')

class ImportPlaylistForm(FlaskForm):
    uri = StringField('Copy the Spotify Playlist ID and paste it below. For an example link https://open.spotify.com/playlist/YmVldmliZV9zdXJwcmlzZQ, id is the last 22 characters, YmVldmliZV9zdXJwcmlzZQ.')
    file = FileField('BeeVibe export:', validators=[FileAllowed(['json'], 'Only exported JSON files are allowed.')])
    import_btn = SubmitField('Import')