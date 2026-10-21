import datetime
from decimal import Decimal

from flask import Blueprint, render_template, redirect, url_for, flash, abort
import flask_login

from . import model


bp = Blueprint("main", __name__)


def is_staff(user):
    return user.role == model.UserRole.management_staff


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


@bp.route("/")
@flask_login.login_required
def index():
    movies = example_data()
    return render_template("main/index.html", movies=movies)


@bp.route("/movie/<int:movie_id>")
@flask_login.login_required
def movie(movie_id):
    movies = {m.id: m for m in example_data()}
    if movie_id not in movies:
        abort(404, "Movie id {} doesn't exist.".format(movie_id))
    return render_template("main/movie.html", movie=movies[movie_id])


@bp.route("/bookings")
@flask_login.login_required
def bookings():
    dune, spirited = example_data()
    upcoming = model.Booking(
        id=1,
        showtime=dune.showtimes[1],
        seats=4,
        ticket_price=Decimal("20.00"),
        free_tickets=1,
        total_price=Decimal("64.00"),
        created_at=datetime.datetime.now(),
    )
    model.BookingFood(
        booking=upcoming,
        food_item=model.FoodItem(name="Large popcorn", price=Decimal("4.00")),
        quantity=1,
        unit_price=Decimal("4.00"),
    )
    past = model.Booking(
        id=2,
        showtime=model.Showtime(
            movie=spirited,
            screen=spirited.showtimes[0].screen,
            starts_at=datetime.datetime.now() - datetime.timedelta(days=7),
        ),
        seats=2,
        ticket_price=Decimal("5.00"),
        free_tickets=0,
        total_price=Decimal("10.00"),
        created_at=datetime.datetime.now() - datetime.timedelta(days=9),
    )
    return render_template("main/bookings.html", upcoming=[upcoming], past=[past])


@bp.route("/staff/movies/new")
@flask_login.login_required
def new_movie():
    if not is_staff(flask_login.current_user):
        abort(403, "Only management staff can add movies.")
    return render_template("main/new_movie.html")


@bp.route("/staff/movies/new", methods=["POST"])
@flask_login.login_required
def new_movie_post():
    if not is_staff(flask_login.current_user):
        abort(403, "Only management staff can add movies.")
    flash("Saving movies is not implemented yet.")
    return redirect(url_for("main.new_movie"))
