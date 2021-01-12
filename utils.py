'''Utility functions for BeeVibe app.

Includes exception-related functions and classes that
are used in multiple files.
'''
from flask import current_app, abort
from psycopg2.errors import UniqueViolation


class DuplicateError(Exception):
    '''Exception for trying to add duplicate songs to a playlist.

    Args:
        msg (str, optional): String explanation for the error.

    Attributes:
        msg (str): String explanation for the error.

    '''

    def __init__(self, msg=None):
        super(DuplicateError, self).__init__()
        if msg:
            self.msg = msg


def handle_db_exception(f):
    '''Handler for possible errors in Database class.

    Used to wrap database functions to catch exceptions raised
    and rollback the changes made to keep DB server running.

    Args:
        f (function): Function to be wrapped.
            This is expected to be a method of Database class.

            The wrapper tries to run the function with given parameters,
            logs and rolls back if an error occurs.

    Returns:
        f: The wrapped function. Wrapper will return the return value of f.

    Raises:
        DuplicateError: If the error is a UniqueViolation, this is passed to
            view function to inform the user.
    '''
    def wrap(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            current_app.logger.warning(e)
            current_app.logger.warning(f"Triggered in {f.__name__}")
            args[0].conn.rollback()
            if isinstance(e, UniqueViolation):
                raise DuplicateError()
            return None
    return wrap
    return f


def error_direction(f):
    '''Handler for possible errors in view functions.

    Used to wrap view functions, logging errors and redirecting
    user to 404 - Not Found page to keep the server running.

    Args:
        f (function): Function to be wrapped.
            This is expected to be a view function.

            The wrapper tries to run the function with given parameters,
            logs and redirects to 404 if an error occurs.

    Returns:
        f: The wrapped function. Wrapper will return the return value
            of f which is usually a rendered template, or 404 page.
    '''
    def wrap(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            current_app.logger.warning(e)
            current_app.logger.warning(f"Triggered in {f.__name__}")
            return abort(404)
    wrap.__name__ = f.__name__
    return wrap
    return f
