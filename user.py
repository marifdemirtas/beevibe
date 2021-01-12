from flask import current_app
from flask_login import UserMixin


class User(UserMixin):
    def __init__(self, s_id, username, email, password):
        self.username = username
        self.password = password
        self.id = s_id
        self.email = email
        self.active = True

    def get_id(self):
        return self.username

    @property
    def is_active(self):
        return self.active


def get_user(username):
    user_data = current_app.config["db"].get_user_tuple(username)
    user = User(*user_data) if user_data else None
    return user
