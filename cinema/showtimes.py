from flask import Blueprint, render_template
import flask_login

from . import db, model
from .permissions import require_staff

bp = Blueprint("showtimes", __name__, url_prefix="/staff/showtimes")


@bp.route("/")
@flask_login.login_required
def showtime_list():
    require_staff()
    return "Showtime management - coming soon"