from decimal import Decimal, InvalidOperation

from flask import Blueprint, render_template, redirect, url_for, flash, request
import flask_login

from . import db, model
from .permissions import require_staff

bp = Blueprint("packages", __name__, url_prefix="/staff/packages")

def all_food_items():
    query = db.select(model.FoodItem).order_by(model.FoodItem.name)
    return db.session.execute(query).scalars().all()

def read_form(package):
    """Checks the form and copies its values into package. Returns error message or None if everything was correct."""  # docstring
    # --- 1. read and check the fields ---
    name=request.form.get("name", "").strip()
    description=request.form.get("description", "").strip()
    if not name or not description:                                     # empty name or description?
        return "Name and description are required"                      # stop here and return error
    try:                                                                # try to convert the numbers 
        price = Decimal(request.form.get("price", ""))                  # int to decimal
        tickets = int(request.form.get("ticket_included", ""))          # str to int
    except (InvalidOperation, ValueError):                              # text isnt a valid num (ie. 'abc' != int)
        return "The price must be a number and ticket count must be a whole number."
    if price < 0 or tickets < 0:
        return "Price and ticket count must be positive numbers."

    # --- 2. read the quantiity box of each food item --- 
    # one quantity box per food item, named qty_<food item id>
    quantities = {}                                                     # empty dir: will map FoodIem --> how many are in the package
    for item in all_food_items():
        try:
            qty = int(request.form.get(f"qty_{item.id}") or 0)          # read box "qty_1", "qty_2"...; empty or missing = 0
        except ValueError:                                              # not a whole numbner
            return "Quantities must be whole numbers."
        if qty < 0:
            return "Quantities cannot be negative."
        if qty > 0:
            quantities[item] = qty                                      # ie. {Popcorn: 1, Soda: 2}
    if tickets == 0 and not quantities:
        return "A package must include at least one ticket or food item."


    # --- 3. Everything is valid, update the package!
    package.name = name                                                 # copy checked values into the Package object
    package.description = description
    package.price = price
    package.ticket_included = tickets
    for old in list(package.items):                                     # remove old contents; list() makes a copy so you can change the original while looping
        package.items.remove(old)                                       # take PackageItem out of the package list
        db.session.delete(old)                                          # and delete that row from the database
    for item, qty in quantities.items():                                # add the new contents: one PackageItem per chosen food item
        package.items.append(model.PackageItem(food_item=item, quantity=qty))  # appending links it to this package (set package_id)
    return None                                                         # no error

@bp.route("/")                                                          # URL /staff/packages/ (GET only)
@flask_login.login_required
def package_list():
    require_staff()                                                     # not staff --> 403 forbidden
    query = db.select(model.Package).order_by(model.Package.name)       # build the query: all packages A-Z
    packages = db.session.execute(query).scalars().all()                # run it
    return render_template("staff/packages/list.html", packages=packages)

@bp.route("/new")
@flask_login.login_required
def new_package():
    require_staff()
    return render_template("staff/packages/form.html", package=None,    # =None tells template its a new package
                           food_items=all_food_items(), quantities={})  # all food items for the boxes; no quantities yet


@bp.route("/new", methods=["POST"])                                     # POST aka form was submitted
@flask_login.login_required
def new_package_post():
    require_staff()
    package = model.Package()                                           # empty Package object (not saved yet)
    error = read_form(package)                                          # check the form and fill the package
    if error:
        flash(error)
        return redirect(url_for("packages.new_package"))
    db.session.add(package)
    db.session.commit()
    flash("Package added.")
    return redirect(url_for("packages.package_list"))                   # redirect after POST --> the list page


@bp.route("/<int:package_id>/edit")                                     # /staff/packages/5/edit; GET shows form prefilled
@flask_login.login_required
def edit_package(package_id):
    require_staff()
    package = db.get_or_404(model.Package, package_id)
    quantities = {line.food_item_id:line.quantity for line in package.items} # directory {food item id: quantity} to prefill the boxes
    return render_template("staff/packages/form.html", package=package, 
                           food_items=all_food_items(), quantities=quantities)

@bp.route("/<int:package_id>/edit", methods=["POST"])                                     # /staff/packages/5/edit; GET shows form prefilled
@flask_login.login_required
def edit_package_post(package_id):
    require_staff()
    package = db.get_or_404(model.Package, package_id)
    error = read_form(package)
    if error:
            db.session.rollback()                                         # undo any half made changes, nothing saved
            flash(error)
            return redirect(url_for("packages.edit_package", package_id=package_id))
    db.session.commit()
    flash("Package updated.")
    return redirect(url_for("packages.package_list"))


@bp.route("/<int:package_id>/delete", methods=["POST"])
@flask_login.login_required
def delete_package(package_id):
    require_staff()
    package = db.get_or_404(model.Package, package_id)
    query = db.select(model.BookingPackage).where(model.BookingPackage.package_id == package_id)
    if db.session.execute(query).first() is not None:
        flash("This package cannot be removed because it is in bookings.")
        return redirect(url_for("packages.package_list"))
    for line in list(package.items):                                      # delete package contents
        db.session.delete(line)
    db.session.delete(package)                                            # delete the package itself
    db.session.commit()
    flash("Package removed.")
    return redirect(url_for("packages.package_list"))