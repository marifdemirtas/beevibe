from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, IntegerField
from wtforms.validators import DataRequired, Optional, Length, Email, NumberRange
from flask_wtf.file import FileField, FileAllowed
from wtforms_components import ColorField


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=100)])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Sign In')


class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=100)])
    email = StringField('E-mail', validators=[DataRequired(), Length(min=4, max=100), Email("Please enter a valid e-mail address.")])
    password = PasswordField('Password', validators=[DataRequired()])
    public = BooleanField('Allow people to see your profile')
    submit = SubmitField('Register')


class CreatePlaylistForm(FlaskForm):
    title = StringField('Title of the playlist', validators=[DataRequired(), Length(min=1, max=100)])
    descr = TextAreaField('Description (optional):', validators=[Optional()])
    image = FileField("Thumbnail image (optional)", validators=[Optional(), FileAllowed(['jpg','jpeg','png'], 'Please upload a .jpg or .png file.')])
    color = ColorField('Background color: ', id="playlist_color")
    privacy = PasswordField('Playlist password (optional):', validators=[Optional()])
    date = IntegerField('Delete this playlist after number of days (optional):', validators=[NumberRange(min=1, max=15, message="Expirable playlists cannot be hosted longer than 15 days or shorter than 1 day."), Optional()])
    commenting = BooleanField('Allow comments: ')
    submit = SubmitField('Create')


class EditPlaylistForm(FlaskForm):
    descr = TextAreaField('Description:', validators=[Optional()])
    color = ColorField('Background color: ', id="playlist_color", validators=[Optional()])
    commenting = BooleanField('Allow comments: ')
    submit = SubmitField('Update')


class ImportPlaylistForm(FlaskForm):
    uri = StringField('Copy the Spotify Playlist URI, starting with spotify:playlist:....')
    file = FileField('BeeVibe export:', validators=[FileAllowed(['json'], 'Only exported JSON files are allowed.')])
    import_btn = SubmitField('Import')


class ProfileUpdateForm(FlaskForm):
    privacy = BooleanField('Can other people see your profile?')
    submit = SubmitField("Update")
