from sre_constants import SUCCESS
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from Models.models import User, ParkingLot, ParkingSpot, Reservation
from Models.models import db
from sqlalchemy.orm import joinedload # To eager load from database
from werkzeug.security import generate_password_hash
from . import admin_bp
from functools import wraps


# ref: "https://github.com/sayan01/bootcamp-july/blob/master/routes.py"
def admin_required(f):
    @wraps(f)
    @login_required # available via flask_login directly
    def func(*args, **kwargs):
        if not current_user.is_admin:
            flash("Admin permission required! Access denied.", 'danger')
            return redirect(url_for('auth_bp.login'))
        if kwargs.get("admin_id") != current_user.id:
            flash("Unauthorized access", 'danger')
            return redirect(url_for('auth_bp.login'))

        return f(*args, **kwargs)
    return func



### Admin Functionalities
@admin_bp.route("/<string:admin_id>/dashboard/")
@admin_required
def admin_dashboard(admin_id):
    parking_lots = ParkingLot.query.all()  
    if not current_user.is_admin or current_user.id != admin_id:
        flash("Admin permission required! Access denied.", 'danger')
        return redirect(url_for('auth_bp.login'))
    return render_template("admin/admin_dashboard.html", admin_id=admin_id, parking_lots=parking_lots)



@admin_bp.route("/<string:admin_id>/editprofile", methods=['GET','POST'])
@admin_required
def edit_admin_profile(admin_id):
    if current_user.id == admin_id:
        if request.method == "POST":
            admin = User.query.filter_by(id=admin_id, is_admin=True).first()
            if admin:
                # Get form data
                full_name = request.form.get("full_name")
                email = request.form.get("email")
                username = request.form.get("username").strip()

                # unique username validation
                existing_user = User.query.filter_by(username=username).first()
                if existing_user and existing_user.id != admin_id:
                    flash("Username already exists. Please choose a different one.", "danger")
                    return redirect(url_for('editProfile', id=id))
                
                # unique email validation
                existing_email = User.query.filter_by(email=email).first()
                if existing_email and existing_email.id != admin_id:
                    flash("Email already exists. Please choose a different one.", "danger")
                    return redirect(url_for('editProfile', id=admin_id))

                # If a new password is provided, hash it
                new_password = request.form.get("new_password")
                admin.password = generate_password_hash(new_password) if new_password.strip() else admin.password

                # Update user details
                admin.full_name = full_name
                admin.email = email
                admin.username = username

                try:
                    db.session.commit()
                except Exception as e:
                    db.session.rollback()
                    flash(f"Error updating profile: {str(e)}", "danger")
                    return redirect(url_for('admin_bp.edit_admin_profile', admin_id=admin_id))

                flash("Profile updated successfully!", "success")
                return redirect(url_for('admin_bp.admin_dashboard', admin_id=admin_id))
            else:
                flash("Permission Denied", "danger")
                return redirect(url_for('auth_bp.login'))
            
        # Handle GET request
        return render_template('admin/edit_admin_profile.html')
    else:
        flash("Permission Denied! Invalid User.", "danger")
        return redirect(url_for('auth_bp.login'))



@admin_bp.route("/<string:admin_id>/search", methods=['GET'])
@admin_required
def search(admin_id):
    from rapidfuzz import fuzz, utils

    query = request.args.get("query", "").strip()
    field = request.args.get("field", "").strip() or "prime_location_name"

    if not query:
        return render_template("admin/admin_search.html", results=["No query passed"], query=query, field=field, admin_id=admin_id)

    processed_query = utils.default_process(query)
    print(processed_query)
    threshold = 90
    results = []

    # ParkingLot Search
    if field in ("parking_lot", "prime_location_name"):
        for lot in ParkingLot.query.all():
            for col in lot.__table__.columns:
                score = fuzz.token_set_ratio(
                    processed_query,
                    str(getattr(lot, col.name)),
                    processor=utils.default_process
                )
                print(score, col.name)
                if score > threshold:
                    results.append(lot)
                    break

    # User Search
    elif field == "user":
        for user in User.query.filter_by(is_admin=False).all():
            for col in user.__table__.columns:
                score = fuzz.token_set_ratio(
                    processed_query,
                    str(getattr(user, col.name)),
                    processor=utils.default_process
                )
                print(score, col.name)
                if score > threshold:
                    results.append(user)
                    break

    # Reservation Search
    elif field == "reservations":
        for reservation in Reservation.query.options(
            joinedload(Reservation.user),
            joinedload(Reservation.spot)
        ).all():
            for col in reservation.__table__.columns:
                score = fuzz.token_set_ratio(
                    processed_query,
                    str(getattr(reservation, col.name)),
                    processor=utils.default_process
                )
                print(score, col.name)
                if score > threshold:
                    results.append(reservation)
                    break

    else:
        flash("Invalid search field", "secondary")

    # Deduplicate by ID
    results_list = list({getattr(obj, 'id'): obj for obj in results}.values())
    results = results_list if results_list else ["Try using better query or field. Could not find a match"]

    return render_template("admin/admin_search.html", results=results, query=query, field=field, admin_id=admin_id)



#Created a summary page
@admin_bp.route("/<string:admin_id>/summary", methods=['GET', 'POST'])
def admin_summary(admin_id):
    admin = User.query.filter_by(id=admin_id, is_admin=True).first_or_404() # Check whether the admin exists
    if current_user.id == admin_id:
        lots_summary = ParkingLot.query.all()
        reservation_summary = Reservation.query.all()
        # print(reservation_summary[-1])
        return render_template("admin/admin_summary.html", lots_summary=lots_summary, reservation_summary=reservation_summary)




@admin_bp.route("/<string:admin_id>/users", methods=['GET', 'POST'])
@admin_required 
def user_list(admin_id):
    if not current_user.is_admin or current_user.id != admin_id:
        flash("Admin permission required! Access denied.", 'danger')
        return redirect(url_for('auth_bp.login'))
    
    users = User.query.filter_by(is_admin=False).all()  # Fetch all non-admin users
    return render_template("admin/user_list.html", users=users)

# CRUD functionalities for parking lots

@admin_bp.route("/<string:admin_id>/createLot", methods=['POST'])
@admin_required 
def create_parking_lot(admin_id):
    if not current_user.is_admin or current_user.id != admin_id:
        flash("Admin permission required! Access denied.", 'danger')
        return redirect(url_for('auth_bp.login'))
    
    prime_location_name = request.form.get("prime_location_name")
    price_per_hour = float(request.form.get("price"))
    address = request.form.get("address")
    pin_code = request.form.get("pin_code")
    max_spots = int(request.form.get("max_spots"))

    new_lot = ParkingLot(
        prime_location_name=prime_location_name,
        price_per_hour=price_per_hour,
        address=address,
        pin_code=pin_code,
        max_spots=max_spots
    )
    try:
        db.session.add(new_lot)
        db.session.flush()  
        # session.flush() sends pending operations (insert, update, delete) to the database,
        # but does not commit them. The changes remain in the current transaction and are not
        # permanently saved or visible to other transactions until session.commit() is called.
        # (Reference: "https://stackoverflow.com/questions/4201455/sqlalchemy-whats-the-difference-between-flush-and-commit")
        try:
            # Create parking spots for the new lot
            for num in range(max_spots):
                new_spot = ParkingSpot(id=num+1, lot_id=new_lot.id)
                db.session.add(new_spot)
            flash("Parking spots created successfully!", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"Error creating parking spots: {str(e)}", "danger")
            return redirect(url_for('admin_bp.admin_dashboard', admin_id=admin_id))
        # Commit the new parking lot and its spots
        db.session.commit()
        flash("Parking Lot created successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error creating parking lot: {str(e)}", "danger")
        
    return redirect(url_for('admin_bp.admin_dashboard', admin_id=admin_id))



@admin_bp.route("/<string:admin_id>/viewLot/<string:lot_id>", methods=['GET'])
@admin_required 
def view_parking_lot(admin_id, lot_id):
    """lazy loading is more about less memory and more computations at each function call, while eager loading 
    would use more memory and more computations when the class is created and less computations when the function is called"""
    parking_lot = ParkingLot.query.options(
        joinedload(ParkingLot.spots).joinedload(ParkingSpot.reservations)
    ).filter_by(id=lot_id).first()

    # Check if the current user is an admin and matches the admin_id
    if not current_user.is_admin or current_user.id != admin_id:
        flash("Admin permission required! Access denied.", 'danger')
        return redirect(url_for('auth_bp.login'))
    
    # Check if the parking lot exists
    if not parking_lot:
        flash("Parking lot not found.", "danger")
        return redirect(url_for('admin_dashboard', admin_id=admin_id))

    return render_template("admin/view_parking_lot.html", parking_lot=parking_lot)


@admin_bp.route("/<string:admin_id>/editLot/<string:lot_id>", methods=['GET', 'POST'])
@admin_required 
def edit_parking_lot(admin_id, lot_id):
    """lazy loading is more about less memory and more computations at each function call, while eager loading 
    would use more memory and more computations when the class is created and less computations when the function is called"""
    parking_lot = ParkingLot.query.options(
        joinedload(ParkingLot.spots).joinedload(ParkingSpot.reservations)
    ).filter_by(id=lot_id).first()

    # Check if the current user is an admin and matches the admin_id
    if not current_user.is_admin or current_user.id != admin_id:
        flash("Admin permission required! Access denied.", 'danger')
        return redirect(url_for('auth_bp.login'))
    
    # Check if the parking lot exists
    if not parking_lot:
        flash("Parking lot not found.", "danger")
        return redirect(url_for('admin_dashboard', admin_id=admin_id))
    
    # Update parking lot details
    if request.method == 'POST':
        new_price = request.form.get("price_per_hour")
        new_prime_location_name = request.form.get("prime_location_name")
        new_address = request.form.get("address")
        new_pin_code = request.form.get("pin_code")
        new_max_spots = int(request.form.get("new_max_spots"))

        # Update the parking lot details
        parking_lot.price_per_hour = new_price
        parking_lot.prime_location_name = new_prime_location_name
        parking_lot.address = new_address
        parking_lot.pin_code = new_pin_code
        updated = parking_lot.update_max_spots(new_max_spots)
        # parking_lot.max_spots = new_max_spots

        if updated:
            try:
                db.session.commit()
                flash("Parking lot details updated successfully!", "success")
            except Exception as e:
                db.session.rollback()
                flash(f"Error updating parking lot details: {str(e)}", "danger")
            return redirect(url_for('admin_bp.view_parking_lot', admin_id=admin_id, lot_id=lot_id))

        else:
            flash("Error updating parking lot details: Cannot update max_spots", "danger")
    
    return render_template("admin/edit_parking_lot.html", parking_lot=parking_lot)



@admin_bp.route("/<string:admin_id>/deleteLot/<string:lot_id>", methods=['POST'])
@admin_required 
def delete_parking_lot(admin_id, lot_id):
    """Delete functionality for parking lots. Possible only when all parking spots are empty."""
    if not current_user.is_admin or current_user.id != admin_id:
        flash("Admin permission required! Access denied.", 'danger')
        return redirect(url_for('auth_bp.login'))
    
    parking_lot = ParkingLot.query.options(joinedload(ParkingLot.spots)).filter_by(id=lot_id).first()

    if not parking_lot:
        flash("Parking lot not found.", "danger")
        return redirect(url_for('admin_bp.admin_dashboard', admin_id=admin_id))
    
    # If all spots are available, delete the parking lot and its spots
    if all(spot.status == 'A' for spot in parking_lot.spots):
        try:
            for spot in parking_lot.spots:
                db.session.delete(spot)
            db.session.delete(parking_lot)
            db.session.commit()
            flash("Parking lot and its spots deleted successfully.", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"Error deleting parking lot: {str(e)}", "danger")
        return redirect(url_for('admin_bp.admin_dashboard', admin_id=admin_id))

    else:
        flash("Cannot delete lot: Some spots are occupied.", "danger")
        return redirect(url_for('admin_bp.admin_dashboard', admin_id=current_user.id))

    

# On parking spots no create and update is allowed, so only read and delete.
@admin_bp.route("/<string:admin_id>/viewLot/<string:lot_id>/viewSpot/<string:spot_id>", methods=['GET'])
@admin_required 
def view_parking_spot(admin_id, lot_id, spot_id):
    if not current_user.is_admin or current_user.id != admin_id:
        flash("Admin permission required! Access denied.", 'danger')
        return redirect(url_for('auth_bp.login'))

    parking_lot = ParkingLot.query.filter_by(id=lot_id).first()
    if not parking_lot:
        flash("Parking lot not found.", "danger")
        return redirect(url_for('admin_dashboard', admin_id=admin_id))

    parking_spot = ParkingSpot.query.filter_by(id=spot_id, lot_id=lot_id).first()
    if not parking_spot:
        flash("Parking spot not found.", "danger")
        return redirect(url_for('view_parking_lot', admin_id=admin_id, lot_id=lot_id))

    return render_template("admin/view_parking_spot.html", parking_lot=parking_lot, parking_spot=parking_spot)


@admin_bp.route("/<string:admin_id>/viewLot/<string:lot_id>/deleteSpot/<string:spot_id>", methods=['POST'])
@admin_required 
def delete_parking_spot(admin_id, spot_id, lot_id):
    if not current_user.is_admin or current_user.id != admin_id:
        flash("Admin permission required! Access denied.", 'danger')
        return redirect(url_for('auth_bp.login'))

    parking_lot = ParkingLot.query.filter_by(id=lot_id).first()
    if not parking_lot:
        flash("Parking lot not found.", "danger")
        return redirect(url_for('admin_bp.admin_dashboard', admin_id=admin_id))

    parking_spot = ParkingSpot.query.filter_by(id=spot_id, lot_id=lot_id).first()
    if not parking_spot:
        flash("Parking spot not found.", "danger")
        return redirect(url_for('admin_bp.view_parking_lot', admin_id=admin_id, lot_id=lot_id))

    try:
        if parking_spot.is_available():
            db.session.delete(parking_spot)
            # reduce the max_spots from Parking Lot
            parking_lot.max_spots -= 1  # Decrease the max_spots count
            if parking_lot.max_spots == 0:
                db.session.delete(parking_lot)
            db.session.commit()
            flash("Parking spot deleted successfully.", "success")
        else:
            flash("Cannot delete spot: It is currently occupied.", "danger")
    
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting parking spot: {str(e)}", "danger")

    return redirect(url_for('admin_bp.view_parking_lot', admin_id=admin_id, lot_id=lot_id))