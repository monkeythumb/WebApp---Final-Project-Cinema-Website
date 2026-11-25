import datetime
from decimal import Decimal

from flask import Blueprint, render_template, redirect, url_for, flash, abort, request
import flask_login

from . import db, model
from .permissions import is_staff, require_staff


bp = Blueprint("main", __name__)


# Example data for the first checkpoint: these objects are NOT stored in the
# database. The controllers will query the database in the next iterations.
def example_data():
    today = datetime.datetime.now().replace(minute=0, second=0, microsecond=0)
    sala1 = model.Screen(id=1, name="Sala 1", capacity=120)
    sala2 = model.Screen(id=2, name="Sala 2", capacity=80)
    dune = model.Movie(
        id=1,
        title="Dune: Part Two",
        synopsis="Paul Atreides unites with the Fremen to take revenge on those who destroyed his family.",
        duration_minutes=166,
        age_rating="+12",
        genre="Science fiction",
        director="Denis Villeneuve",
        actors="Timothée Chalamet, Zendaya, Rebecca Ferguson",
        release_year=2024,
    )
    spirited = model.Movie(
        id=2,
        title="Spirited Away",
        synopsis="A girl wanders into a world of spirits and must work to free herself and her parents.",
        duration_minutes=125,
        age_rating="TP",
        genre="Animation",
        director="Hayao Miyazaki",
        actors="Rumi Hiiragi, Miyu Irino",
        release_year=2001,
    )
    model.Showtime(id=1, movie=dune, screen=sala1, starts_at=today.replace(hour=18), is_3d=False)
    model.Showtime(id=2, movie=dune, screen=sala1, starts_at=today.replace(hour=21, minute=30), is_3d=True)
    model.Showtime(id=3, movie=dune, screen=sala2, starts_at=(today + datetime.timedelta(days=1)).replace(hour=19), is_3d=False)
    model.Showtime(id=4, movie=spirited, screen=sala2, starts_at=today.replace(hour=17), is_3d=False)
    model.Showtime(id=5, movie=spirited, screen=sala2, starts_at=(today + datetime.timedelta(days=1)).replace(hour=16), is_3d=False)
    return [dune, spirited]

# controller
@bp.route("/")                                                            # connects the url to this function GET only
@flask_login.login_required                                               # if not logged in, send them to the login page instead of running the function
def index():                                                              # the controller with no paramaters bc the URL has no variable part
    query = db.select(model.Movie).order_by(model.Movie.title)            # select rows from the movie table :: in alphabetical order by title 
    movies = db.session.execute(query).scalars().all()                    # turns the result into a list of Movie objects
    return render_template("main/index.html", movies=movies)              # fills in the template, which receives a variable called 'movies' and returns the HTML page 


@bp.route("/movie/<int:movie_id>")                                        # function handles /movie/< # >
@flask_login.login_required                                               # only logged in users
def movie(movie_id):                                                      # function with parameter of the movie id
    movie = db.get_or_404(model.Movie, movie_id)                          # store in "movie" the Movie with that id or 404 error
    return render_template("main/movie.html", movie=movie)     # send back the page, giving it "movie"


@bp.route("/bookings")
@flask_login.login_required
def bookings():
    query = (
        db.select(model.Booking)
        .join(model.Booking.showtime)
        .where(model.Booking.user == flask_login.current_user)
        .order_by(model.Showtime.starts_at)
    )
    my_bookings = db.session.execute(query).scalars().all()
    now = datetime.datetime.now()
    upcoming = [b for b in my_bookings if b.showtime.starts_at >= now]
    past = [b for b in my_bookings if b.showtime.starts_at < now]
    return render_template("main/bookings.html", upcoming=upcoming, past=past)


@bp.route("/staff/movies/new")
@flask_login.login_required
def new_movie():
    require_staff()
    return render_template("main/new_movie.html")

# AI API Poster help
@bp.route("/staff/movies/new", methods=["POST"])
@flask_login.login_required
def new_movie_post():
    require_staff()

    # numbers come from the form as txt so convertthem and reject bad input
    try:
        duration = int(request.form.get("duration_minutes"))
        year = int(request.form.get("release_year"))
    except (TypeError, ValueError):
        flash("Duration and release year must be whole numbers") 
        return redirect(url_for("main.new_movie"))

    poster_data = None
    poster_mime_type = None
    poster = request.files.get("poster")
    if poster and poster.filename:
        if not poster.mimetype.startswith("image/"):
            flash("The poster must be an image file.")
            return redirect(url_for("main.new_movie"))
        poster_data = poster.read()
        if len(poster_data) > model.Movie.MAX_POSTER_SIZE:
            flash("The poster is too big (maximum 1 MB)")
            return redirect(url_for("main.new_movie"))
        poster_mime_type = poster.mimetype

    movie = model.Movie(
        title=request.form.get("title"),
        synopsis=request.form.get("synopsis"),
        duration_minutes=duration,
        age_rating=request.form.get("age_rating"),
        genre=request.form.get("genre"),
        director=request.form.get("director"),
        actors=request.form.get("actors", ""),
        release_year=year,
        poster_data=poster_data,
        poster_mime_type=poster_mime_type,
    )

    db.session.add(movie)
    db.session.commit()
    flash("Movie added!")
    return redirect(url_for("main.movie", movie_id=movie.id))