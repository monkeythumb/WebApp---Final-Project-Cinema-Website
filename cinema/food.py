from flask import Blueprint, render_template
import flask_login

from . import db, model
from .permissions import require_staff

bp = Blueprint("food", __name__, url_prefix="/staff/food")


@bp.route("/")
@flask_login.login_required
def food_list():
    require_staff()
    return "Food management - coming soon"