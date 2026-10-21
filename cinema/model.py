import datetime
import enum
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import String, Text, DateTime, ForeignKey, LargeBinary, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

import flask_login

from . import db

class UserRole(enum.Enum):
    customer = 1
    management_staff = 2

class User(flask_login.UserMixin, db.Model):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(128), unique=True)
    name: Mapped[str] = mapped_column(String(64))
    password: Mapped[str] = mapped_column(String(512))
    bookings: Mapped[List["Booking"]] = relationship(back_populates="user")
    role: Mapped[UserRole]

class Movie(db.Model):
    MAX_POSTER_SIZE = 1024 * 1024 # 1 MB
    __tablename__ = "movies"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(64))
    synopsis: Mapped[str] = mapped_column(Text)
    duration_minutes: Mapped[int]
    age_rating: Mapped[str] = mapped_column(String(16))
    genre: Mapped[str] = mapped_column(String(64))
    director: Mapped[str] = mapped_column(String(64))
    actors: Mapped[str] = mapped_column(Text)
    release_year: Mapped[int]
    poster_data: Mapped[Optional[bytes]] = mapped_column(LargeBinary(MAX_POSTER_SIZE))
    poster_mime_type: Mapped[Optional[str]] = mapped_column(String(128))
    showtimes: Mapped[List["Showtime"]] = relationship(back_populates="movie")

class Screen(db.Model):
    __tablename__= "screens"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(32), unique=True)
    capacity: Mapped[int] 
    showtimes: Mapped[List["Showtime"]] = relationship(back_populates="screen")

class Showtime(db.Model):
    __tablename__ = "showtimes"
    id: Mapped[int] = mapped_column(primary_key=True)
    movie_id: Mapped[int] = mapped_column(ForeignKey("movies.id"))
    movie: Mapped["Movie"] = relationship(back_populates="showtimes")
    screen_id: Mapped[int] = mapped_column(ForeignKey("screens.id"))
    screen: Mapped["Screen"] = relationship(back_populates="showtimes")
    starts_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True))
    is_3d: Mapped[bool] = mapped_column(default=False)
    bookings: Mapped[List["Booking"]] = relationship(back_populates="showtime")

class TicketPrice(db.Model):
    __tablename__="ticket_prices"
    id: Mapped[int] = mapped_column(primary_key=True)
    weekday: Mapped[int] = mapped_column(unique=True)
    price: Mapped[Decimal] = mapped_column(Numeric(6,2))

class FoodCategory(enum.Enum):
    drink = 1
    popcorn = 2
    candy = 3

class FoodItem(db.Model):
    __tablename__="food_items"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(64))
    description: Mapped[str] = mapped_column(Text)
    price: Mapped[Decimal] = mapped_column(Numeric(6, 2))
    category: Mapped[FoodCategory] 
    free_refill: Mapped[bool] = mapped_column(default=False)

class Package(db.Model):
    __tablename__="packages"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(64))
    description: Mapped[str] = mapped_column(Text)
    price: Mapped[Decimal] = mapped_column(Numeric(6,2))
    ticket_included: Mapped[int]
    items: Mapped[List["PackageItem"]] = relationship(back_populates="package")

class PackageItem(db.Model):
    __tablename__="package_items"
    id: Mapped[int] = mapped_column(primary_key=True)
    package_id: Mapped[int] = mapped_column(ForeignKey("packages.id"))
    package: Mapped["Package"] = relationship(back_populates="items")
    food_item_id: Mapped[int] = mapped_column(ForeignKey("food_items.id"))
    food_item: Mapped["FoodItem"] = relationship()
    quantity: Mapped[int]


class Booking(db.Model):
    __tablename__ = "bookings"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    user: Mapped["User"] = relationship(back_populates="bookings")
    showtime_id: Mapped[int] = mapped_column(ForeignKey("showtimes.id"))
    showtime: Mapped["Showtime"] = relationship(back_populates="bookings")
    seats: Mapped[int]
    ticket_price: Mapped[Decimal] = mapped_column(Numeric(6, 2))
    free_tickets: Mapped[int] = mapped_column(default=0)
    total_price: Mapped[Decimal] = mapped_column(Numeric(6, 2))
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    foods: Mapped[List["BookingFood"]] = relationship(back_populates="booking")
    packages: Mapped[List["BookingPackage"]] = relationship(back_populates="booking")

class BookingFood(db.Model):
    __tablename__="booking_foods"
    id: Mapped[int] = mapped_column(primary_key=True)
    booking_id: Mapped[int] = mapped_column(ForeignKey("bookings.id"))
    booking: Mapped["Booking"] = relationship(back_populates="foods")
    food_item_id: Mapped[int] = mapped_column(ForeignKey("food_items.id"))
    food_item: Mapped["FoodItem"] = relationship()
    quantity: Mapped[int]
    unit_price: Mapped[Decimal] = mapped_column(Numeric(6, 2))
    
class BookingPackage(db.Model):
    __tablename__ = "booking_packages"
    id: Mapped[int] = mapped_column(primary_key=True)
    booking_id: Mapped[int] = mapped_column(ForeignKey("bookings.id"))
    booking: Mapped["Booking"] = relationship(back_populates="packages")
    package_id: Mapped[int] = mapped_column(ForeignKey("packages.id"))
    package: Mapped["Package"] = relationship()
    quantity: Mapped[int]
    unit_price: Mapped[Decimal] = mapped_column(Numeric(6, 2))
