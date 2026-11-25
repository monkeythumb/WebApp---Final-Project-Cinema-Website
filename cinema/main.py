import datetime

from flask import Blueprint, render_template, redirect, url_for, flash, abort, request, Response
import flask_login

from . import db, model
from .permissions import is_staff, require_staff

bp = Blueprint("main", __name__)

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
    return render_template("main/movie.html", movie=movie)                # send back the page, giving it "movie"

@bp.route("/movie/<int:movie_id>/poster")
@flask_login.login_required
def movie_poster(movie_id):
    movie = db.get_or_404(model.Movie, movie_id)
    if movie.poster_data is None:
        abort(404)
    return Response(movie.poster_data, mimetype=movie.poster_mime_type)   # builds an HTTP response whose body is the raw image bytes, with ContentType
                                                                          # header taken from the saved MIME type, so browser knows its an image


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
    poster_mime_type = None  # LargeBinary
    poster = request.files.get("poster")                    # gets uploaded file from the form. text->request.form, files->requests.files
    if poster and poster.filename:                          # no poster if poster.filename is empty
        if not poster.mimetype.startswith("image/"):        # mimetype=file's type as browser reports it
            flash("The poster must be an image file.")      
            return redirect(url_for("main.new_movie"))
        poster_data = poster.read()                         # reads file's contents as bytes which gets saved in poster_data
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