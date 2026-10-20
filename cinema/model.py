import datetime
from typing import List, Optional

from sqlalchemy import String, DateTime, ForeignKey, LargeBinary
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

import flask_login

from . import db


class User(flask_login.UserMixin, db.Model):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(128), unique=True)
    name: Mapped[str] = mapped_column(String(64))
    password: Mapped[str] = mapped_column(String(512))
    posts: Mapped[List["Post"]] = relationship(back_populates="user")
    profile: Mapped["UserProfile"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )

class UserProfile(db.Model):
    __tablename__ = "user_profiles"
    MAX_PICTURE_SIZE = 256 * 1024 # maximum picture size: 256 KiB

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    user: Mapped["User"] = relationship(back_populates="profile")
    description: Mapped[str] = mapped_column(String(4192), server_default="")
    picture_mime_type: Mapped[Optional[str]] = mapped_column(String(128))
    picture_data: Mapped[Optional[bytes]] = mapped_column(LargeBinary(MAX_PICTURE_SIZE))

class Post(db.Model):
    __tablename__ = "posts"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    user: Mapped["User"] = relationship(back_populates="posts")
    text: Mapped[str] = mapped_column(String(512))
    timestamp: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    response_to_id: Mapped[Optional[int]] = mapped_column(ForeignKey("posts.id"))
    response_to: Mapped["Post"] = relationship(
        back_populates="responses", remote_side=[id]
    )
    responses: Mapped[List["Post"]] = relationship(
        back_populates="response_to", remote_side=[response_to_id]
    )