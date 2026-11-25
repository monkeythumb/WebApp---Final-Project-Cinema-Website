import datetime

from flask import Blueprint, render_template, redirect, url_for, flash, request
import flask_login

from . import db, model
from .permissions import require_staff

bp = Blueprint("showtimes", __name__, url_prefix="/staff/showtimes")

DATETIME_FORMAT = "%Y-%m-%dT%H:%M"  # what <input type="datetime-local"> sends
CLEANUP_MINUTES = 0  # gap required between two showtimes on the same screen (e.g. 15)


def naive(dt):
    # The column is timezone-aware but the form sends naive local times.
    # Strip tzinfo so we can always compare values with each other.
    return dt.replace(tzinfo=None)


def parse_form(form):
    """Validate the submitted form. Returns (data, errors)."""
    errors = []

    try:
        movie = db.session.get(model.Movie, int(form.get("movie_id", "")))
    except ValueError:
        movie = None
    if movie is None:
        errors.append("Choose a valid movie.")

    try:
        screen = db.session.get(model.Screen, int(form.get("screen_id", "")))
    except ValueError:
        screen = None
    if screen is None:
        errors.append("Choose a valid screen.")

    try:
        starts_at = datetime.datetime.strptime(form.get("starts_at", ""), DATETIME_FORMAT)
    except ValueError:
        starts_at = None
        errors.append("Enter a valid date and time.")

    data = {
        "movie": movie,
        "screen": screen,
        "starts_at": starts_at,
        "is_3d": "is_3d" in form,
    }
    return data, errors


def find_overlap(movie, screen, starts_at, ignore_id=None):
    """Return a showtime on the same screen that overlaps the new one, or None."""
    margin = datetime.timedelta(minutes=CLEANUP_MINUTES)
    ends_at = starts_at + datetime.timedelta(minutes=movie.duration_minutes) + margin

    # Only showtimes close in time can overlap, so don't load the whole table.
    query = db.select(model.Showtime).where(
        model.Showtime.screen_id == screen.id,
        model.Showtime.starts_at > starts_at - datetime.timedelta(days=2),
        model.Showtime.starts_at < ends_at,
    )
    if ignore_id is not None:
        query = query.where(model.Showtime.id != ignore_id)

    for other in db.session.execute(query).scalars():
        other_start = naive(other.starts_at)
        other_end = other_start + datetime.timedelta(minutes=other.movie.duration_minutes) + margin
        if starts_at < other_end and other_start < ends_at:
            return other
    return None


def showtime_to_form(showtime):
    """Values used to pre-fill the form when editing."""
    return {
        "movie_id": showtime.movie_id,
        "screen_id": showtime.screen_id,
        "starts_at": showtime.starts_at.strftime(DATETIME_FORMAT),
        "is_3d": showtime.is_3d,
    }


def render_form(form, showtime=None, status=200):
    if showtime is None:
        heading = "Add showtime"
        action = url_for("showtimes.new_showtime_post")
    else:
        heading = "Edit showtime"
        action = url_for("showtimes.edit_showtime_post", showtime_id=showtime.id)
    movies = db.session.execute(db.select(model.Movie).order_by(model.Movie.title)).scalars().all()
    screens = db.session.execute(db.select(model.Screen).order_by(model.Screen.name)).scalars().all()
    return (
        render_template(
            "staff/showtimes/form.html",
            form=form,
            heading=heading,
            action=action,
            movies=movies,
            screens=screens,
        ),
        status,
    )


def describe(showtime):
    return "{} on {} at {}".format(
        showtime.movie.title,
        showtime.screen.name,
        showtime.starts_at.strftime("%a %d/%m/%Y %H:%M"),
    )


@bp.route("/")
@flask_login.login_required
def showtime_list():
    require_staff()
    query = db.select(model.Showtime).order_by(model.Showtime.starts_at)
    showtimes = db.session.execute(query).scalars().all()
    return render_template(
        "staff/showtimes/list.html",
        showtimes=showtimes,
        now=datetime.datetime.now(),
        naive=naive,
    )


@bp.route("/new")
@flask_login.login_required
def new_showtime():
    require_staff()
    return render_form({})


@bp.route("/new", methods=["POST"])
@flask_login.login_required
def new_showtime_post():
    require_staff()
    data, errors = parse_form(request.form)
    if not errors:
        if data["starts_at"] < datetime.datetime.now():
            errors.append("The showtime can't start in the past.")
        else:
            other = find_overlap(data["movie"], data["screen"], data["starts_at"])
            if other:
                errors.append("That screen is already in use then: {}.".format(describe(other)))
    if errors:
        for error in errors:
            flash(error)
        return render_form(request.form, status=400)

    showtime = model.Showtime(**data)
    db.session.add(showtime)
    db.session.commit()
    flash("Showtime created: {}.".format(describe(showtime)))
    return redirect(url_for("showtimes.showtime_list"))


@bp.route("/<int:showtime_id>/edit")
@flask_login.login_required
def edit_showtime(showtime_id):
    require_staff()
    showtime = db.get_or_404(model.Showtime, showtime_id)
    if showtime.bookings:
        flash("This showtime already has bookings and can't be edited.")
        return redirect(url_for("showtimes.showtime_list"))
    return render_form(showtime_to_form(showtime), showtime)


@bp.route("/<int:showtime_id>/edit", methods=["POST"])
@flask_login.login_required
def edit_showtime_post(showtime_id):
    require_staff()
    showtime = db.get_or_404(model.Showtime, showtime_id)
    if showtime.bookings:
        flash("This showtime already has bookings and can't be edited.")
        return redirect(url_for("showtimes.showtime_list"))

    data, errors = parse_form(request.form)
    if not errors:
        other = find_overlap(data["movie"], data["screen"], data["starts_at"], ignore_id=showtime.id)
        if other:
            errors.append("That screen is already in use then: {}.".format(describe(other)))
    if errors:
        for error in errors:
            flash(error)
        return render_form(request.form, showtime, status=400)

    for key, value in data.items():
        setattr(showtime, key, value)
    db.session.commit()
    flash("Showtime updated: {}.".format(describe(showtime)))
    return redirect(url_for("showtimes.showtime_list"))


@bp.route("/<int:showtime_id>/delete", methods=["POST"])
@flask_login.login_required
def delete_showtime(showtime_id):
    require_staff()
    showtime = db.get_or_404(model.Showtime, showtime_id)
    if showtime.bookings:
        flash("This showtime already has bookings and can't be deleted.")
        return redirect(url_for("showtimes.showtime_list"))
    text = describe(showtime)
    db.session.delete(showtime)
    db.session.commit()
    flash("Showtime deleted: {}.".format(text))
    return redirect(url_for("showtimes.showtime_list"))