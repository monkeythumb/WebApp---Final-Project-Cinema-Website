from decimal import Decimal, InvalidOperation

from flask import Blueprint, render_template, redirect, url_for, flash, request
import flask_login
from sqlalchemy import func

from . import db, model
from .permissions import require_staff

bp = Blueprint("food", __name__, url_prefix="/staff/food")

MAX_PRICE = Decimal("9999.99")  # the column is Numeric(6, 2)


def parse_form(form):
    """Validate the submitted form. Returns (data, errors)."""
    errors = []

    name = form.get("name", "").strip()
    if not name:
        errors.append("The name is required.")
    elif len(name) > 64:
        errors.append("The name can have at most 64 characters.")

    description = form.get("description", "").strip()
    if not description:
        errors.append("The description is required.")

    try:
        price = Decimal(form.get("price", "").strip().replace(",", "."))
        if (
            not price.is_finite()
            or price < 0
            or price > MAX_PRICE
            or price.as_tuple().exponent < -2
        ):
            raise InvalidOperation
    except InvalidOperation:
        price = None
        errors.append("The price must be a number between 0 and 9999.99 with at most 2 decimals.")

    try:
        category = model.FoodCategory[form.get("category", "")]
    except KeyError:
        category = None
        errors.append("Choose a valid category.")

    data = {
        "name": name,
        "description": description,
        "price": price,
        "category": category,
        "free_refill": "free_refill" in form,
    }
    return data, errors


def item_to_form(item):
    """Values used to pre-fill the form when editing."""
    return {
        "name": item.name,
        "description": item.description,
        "price": "%.2f" % item.price,
        "category": item.category.name,
        "free_refill": item.free_refill,
    }


def render_form(form, item=None, status=200):
    if item is None:
        heading = "Add food item"
        action = url_for("food.new_food_post")
    else:
        heading = "Edit food item"
        action = url_for("food.edit_food_post", food_id=item.id)
    return (
        render_template(
            "staff/food/form.html",
            form=form,
            heading=heading,
            action=action,
            categories=list(model.FoodCategory),
        ),
        status,
    )


@bp.route("/")
@flask_login.login_required
def food_list():
    require_staff()
    query = db.select(model.FoodItem).order_by(model.FoodItem.category, model.FoodItem.name)
    items = db.session.execute(query).scalars().all()
    return render_template("staff/food/list.html", items=items)


@bp.route("/new")
@flask_login.login_required
def new_food():
    require_staff()
    return render_form({})


@bp.route("/new", methods=["POST"])
@flask_login.login_required
def new_food_post():
    require_staff()
    data, errors = parse_form(request.form)
    if errors:
        for error in errors:
            flash(error)
        return render_form(request.form, status=400)
    item = model.FoodItem(**data)
    db.session.add(item)
    db.session.commit()
    flash("Food item '{}' created.".format(item.name))
    return redirect(url_for("food.food_list"))


@bp.route("/<int:food_id>/edit")
@flask_login.login_required
def edit_food(food_id):
    require_staff()
    item = db.get_or_404(model.FoodItem, food_id)
    return render_form(item_to_form(item), item)


@bp.route("/<int:food_id>/edit", methods=["POST"])
@flask_login.login_required
def edit_food_post(food_id):
    require_staff()
    item = db.get_or_404(model.FoodItem, food_id)
    data, errors = parse_form(request.form)
    if errors:
        for error in errors:
            flash(error)
        return render_form(request.form, item, status=400)
    for key, value in data.items():
        setattr(item, key, value)
    db.session.commit()
    flash("Food item '{}' updated.".format(item.name))
    return redirect(url_for("food.food_list"))


@bp.route("/<int:food_id>/delete", methods=["POST"])
@flask_login.login_required
def delete_food(food_id):
    require_staff()
    item = db.get_or_404(model.FoodItem, food_id)

    # Foreign keys would make the delete fail (and we don't want to rewrite
    # the history of past bookings), so refuse if the item is in use.
    in_bookings = db.session.scalar(
        db.select(func.count())
        .select_from(model.BookingFood)
        .where(model.BookingFood.food_item_id == item.id)
    )
    in_packages = db.session.scalar(
        db.select(func.count())
        .select_from(model.PackageItem)
        .where(model.PackageItem.food_item_id == item.id)
    )
    if in_bookings or in_packages:
        flash(
            "'{}' can't be deleted because it is used in {} booking line(s) "
            "and {} package(s).".format(item.name, in_bookings, in_packages)
        )
        return redirect(url_for("food.food_list"))

    name = item.name
    db.session.delete(item)
    db.session.commit()
    flash("Food item '{}' deleted.".format(name))
    return redirect(url_for("food.food_list"))