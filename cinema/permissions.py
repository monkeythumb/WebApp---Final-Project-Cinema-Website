from flask import abort
import flask_login

from . import model

def is_staff(user):
    return user.role == model.UserRole.management_staff


def require_staff():
    # Stops anyone who isn't management staff with 403 Forbidden.
    # Call it on the first line of every staff controller.
    if not is_staff(flask_login.current_user):
        abort(403, "Only management staff can access this page.")