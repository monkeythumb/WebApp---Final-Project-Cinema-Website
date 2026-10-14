import datetime
import dateutil.tz

from flask import Blueprint, render_template


from . import model

bp = Blueprint("main", __name__)


@bp.route("/")
def index():
    user = model.User(email="mary@example.com", name="mary")
    posts = [
        model.Post(
            user=user,
            text="Test post",
            timestamp=datetime.datetime.now(dateutil.tz.tzlocal()),
        ),
        model.Post(
            user=user,
            text="Another post",
            timestamp=datetime.datetime.now(dateutil.tz.tzlocal()),
        ),
        model.Post(
            user=user,
            text="E-Post",
            timestamp=datetime.datetime.now(dateutil.tz.tzlocal()),
        ),
    ]
    return render_template("main/index.html", posts=posts)


@bp.route("/profile")
def profile():
    user = model.User(email="mary@example.com", name="mary")
    posts = [
        model.Post(
            user=user,
            text="Finally finished the HTML and CSS lab.",
            timestamp=datetime.datetime.now(dateutil.tz.tzlocal()),
        ),
        model.Post(
            user=user,
            text="Does anyone have good notes on TLS handshakes?",
            timestamp=datetime.datetime.now(dateutil.tz.tzlocal()),
        ),
    ]
    return render_template("main/profile.html", user=user, posts=posts)


@bp.route("/post")
def post():
    user = model.User(email="mary@example.com", name="mary")
    other_user = model.User(email="john@example.com", name="john")
    original = model.Post(
        user=user,
        text="Finally finished the HTML and CSS lab.",
        timestamp=datetime.datetime.now(dateutil.tz.tzlocal()),
    )
    responses = [
        model.Post(
            user=other_user,
            text="Same here, the CSS part took me longer than the HTML.",
            timestamp=datetime.datetime.now(dateutil.tz.tzlocal()),
        ),
        model.Post(
            user=other_user,
            text="Good luck with Flask!",
            timestamp=datetime.datetime.now(dateutil.tz.tzlocal()),
        ),
    ]
    return render_template("main/post.html", post=original, posts=responses)