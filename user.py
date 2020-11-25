from flask import current_app
from flask_login import UserMixin


class User(UserMixin):
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.active = True

    def get_id(self):
        return self.username

    @property
    def is_active(self):
        return self.active


def get_user(user_id):
    password = current_app.config["db"].get_user_password(user_id)
    user = User(user_id, password) if password else None
    return user
