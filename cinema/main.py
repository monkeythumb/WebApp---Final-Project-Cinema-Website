import datetime
import dateutil.tz

from flask import Blueprint, render_template, request, redirect, url_for
# request - reading the form data
# redirect, url_for - sending the browser to the post's page
# db - saving to the database
import flask_login

from . import db
from . import model


bp = Blueprint("main", __name__)


@bp.route("/")
@flask_login.login_required
def index():
    query = db.select(model.Post).order_by(model.Post.timestamp.desc()).limit(10)
    posts = db.session.execute(query).scalars().all()
    return render_template("main/index.html", posts=posts)


@bp.route("/profile")
@flask_login.login_required
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


@bp.route("/post/<int:post_id>")
@flask_login.login_required
def post(post_id):
    post = db.get_or_404(model.Post, post_id)
    return render_template("main/post.html", post=post)


@bp.route("/post/new", methods=["POST"])
@flask_login.login_required 
def new_post():
    text = request.form.get("text") # read the text from the form
    # create post object: 
    post = model.Post(
        user=flask_login.current_user, # current_user - loggedin user from User row from the database
        text=text,
        timestamp=datetime.datetime.now(dateutil.tz.tzlocal()), # datetime and dateutil - timestamps imported from main.py
    )

    db.session.add(post)
    db.session.commit()

    return redirect(url_for("main.post", post_id=post.id))
