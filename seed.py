# seed script to fill the empty database with starting data
import getpass
from decimal import Decimal

from werkzeug.security import generate_password_hash

from cinema import create_app, db, model

app = create_app()

with app.app_context():
    db.create_all()

    if db.session.execute(db.select(model.Screen)).first() is None:
        db.session.add(model.Screen(name="Sala 1", capacity=120))
        db.session.add(model.Screen(name="Sala 2", capacity=85))
        db.session.add(model.Screen(name="Sala 3", capacity=50))
        print("Added three screens")

    if db.session.execute(db.select(model.TicketPrice)).first() is None:
        prices = ["8.00", "8.00", "5.50", "8.00", "8.00", "8.00", "8.00"] # mon-sun
        for weekday, price in enumerate(prices):
            db.session.add(model.TicketPrice(weekday=weekday, price=Decimal(price)))
        print("Added ticket prices")

    if db.session.execute(db.select(model.Movie)).first() is None:
        db.session.add(model.Movie(
            title="Dune: Part Two",
            synopsis="Paul Atreides unites with the Fremen to take revenge on those who destroyed his family.",
            duration_minutes=166, age_rating="+12", genre="Science fiction",
            director="Denis Villeneuve", actors="Timothée Chalamet, Zendaya, Rebecca Ferguson",
            release_year=2024,
        ))
        db.session.add(model.Movie(
            title="Spirited Away",
            synopsis="A girl wanders into a world of spirits and must work to free herself and her parents.",
            duration_minutes=125, age_rating="TP", genre="Animation",
            director="Hayao Miyazaki", actors="Rumi Hiiragi, Miyu Irino",
            release_year=2001,
        ))
        print("Added 2 movies")

    db.session.commit()

    if input("Create a staff account? (y/n) ").strip().lower() == "y":
        email = input("Staff email: ").strip()
        exists = db.session.execute(db.select(model.User).where(model.User.email == email)).scalar_one_or_none()
        if exists:
            print("That email already exists.")
        else:
            db.session.add(model.User(
                email=email,
                name=input("Staff name: ").strip(),
                password=generate_password_hash(getpass.getpass("Password: ")),
                role=model.UserRole.management_staff,
            ))
            db.session.commit()
            print("Staff account created.")
