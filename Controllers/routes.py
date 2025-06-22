from hmac import new
from flask import render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import joinedload  # To eager load from database
from app import app, db, login_manager
from Models.models import User, ParkingLot, ParkingSpot, Reservation


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)



# routes that does not need authentications
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/features")
def features():
    return render_template("features.html")


@app.route("/services")
def services():
    return "<h1>Available Services</h1>"

@app.route("/stats")
def stats():
    return "Stats"


#? auth.py

@app.route("/register", methods=['GET','POST'])
def register():
    if request.method == "POST":
        username = request.form.get("username").strip() # strip to ensure no extra space
        # unique username validation
        user = User.query.filter_by(username=username).first()
        if user:
            flash("Username already exists! Choose another username", "danger")
            return redirect(url_for('register'))
        
        # unique email validation
        email = request.form.get("email")
        user = User.query.filter_by(email=email).first()
        if user:
            flash("Account already exist with this mail. Kindly login to proceed furthur", "secondary")
            return redirect(url_for('login'))
        
        pwd = request.form.get("password")
        password = generate_password_hash(pwd)

        new_user = User(username=username, email=email, password=password)
        db.session.add(new_user)
        db.session.commit()
        flash("Registration successful!", "success")
        return redirect(url_for('login'))
    
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username").strip()
        password = request.form.get("password")
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            flash("Login successful!", "success")
            if user.is_admin:
                return redirect(url_for("admin_dashboard", admin_id = user.id))
            else:
                return redirect(url_for("user_dashboard", user_id = user.id))
        else:
            flash("Invalid credentials", "danger")
            return redirect(url_for("login"))

    return render_template("login.html")




# every other routes that needs authentication will go here


### Admin Functionalities
@app.route("/admin/<string:admin_id>/dashboard/")
@login_required    #TODO: change to `@admin_required`
def admin_dashboard(admin_id):
    if not current_user.is_admin or current_user.id != admin_id:
        flash("Admin permission required! Access denied.", 'danger')
        return redirect(url_for('login'))
    return render_template("admin_dashboard.html")


@app.route("/admin/<string:admin_id>/users", methods=['GET', 'POST'])
@login_required #TODO: change to `@admin_required`
def user_list(admin_id):
    if not current_user.is_admin or current_user.id != admin_id:
        flash("Admin permission required! Access denied.", 'danger')
        return redirect(url_for('login'))
    
    #TODO: Implement flagging users
    
    users = User.query.filter_by(is_admin=False).all()  # Fetch all non-admin users
    return render_template("user_list.html", users=users)



# CRUD functionalities for parking lots

@app.route("/admin/<string:admin_id>/createLot", methods=['POST'])
@login_required #TODO: change to `@admin_required`
def create_parking_lot(admin_id):
    if not current_user.is_admin or current_user.id != admin_id:
        flash("Admin permission required! Access denied.", 'danger')
        return redirect(url_for('login'))
    
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
                new_spot = ParkingSpot(id=num, lot_id=new_lot.id)
                db.session.add(new_spot)
        except Exception as e:
            db.session.rollback()
            flash(f"Error creating parking spots: {str(e)}", "danger")
            return redirect(url_for('admin_dashboard', admin_id=admin_id))
        # Commit the new parking lot and its spots
        db.session.commit()
        flash("Parking Lot created successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error creating parking lot: {str(e)}", "danger")
        return redirect(url_for('admin_dashboard', admin_id=admin_id))
    return redirect(url_for('admin_dashboard', admin_id=admin_id))



@app.route("/admin/<string:admin_id>/viewLot/<string:lot_id>", methods=['GET'])
@login_required #TODO: change to `@admin_required`
def view_parking_lot(admin_id, lot_id):
    """lazy loading is more about less memory and more computations at each function call, while eager loading 
    would use more memory and more computations when the class is created and less computations when the function is called"""
    parking_lot = ParkingLot.query.options(
        joinedload(ParkingLot.spots).joinedload(ParkingSpot.reservations)
    ).filter_by(id=lot_id).first()

    # Check if the current user is an admin and matches the admin_id
    if not current_user.is_admin or current_user.id != admin_id:
        flash("Admin permission required! Access denied.", 'danger')
        return redirect(url_for('login'))
    
    # Check if the parking lot exists
    if not parking_lot:
        flash("Parking lot not found.", "danger")
        return redirect(url_for('admin_dashboard', admin_id=admin_id))

    return render_template("view_parking_lot.html", parking_lot=parking_lot)


@app.route("/admin/<string:admin_id>/editLot/<string:lot_id>", methods=['GET', 'POST'])
@login_required #TODO: change to `@admin_required`
def edit_parking_lot(admin_id, lot_id):
    """lazy loading is more about less memory and more computations at each function call, while eager loading 
    would use more memory and more computations when the class is created and less computations when the function is called"""
    parking_lot = ParkingLot.query.options(
        joinedload(ParkingLot.spots).joinedload(ParkingSpot.reservations)
    ).filter_by(id=lot_id).first()

    # Check if the current user is an admin and matches the admin_id
    if not current_user.is_admin or current_user.id != admin_id:
        flash("Admin permission required! Access denied.", 'danger')
        return redirect(url_for('login'))
    
    # Check if the parking lot exists
    if not parking_lot:
        flash("Parking lot not found.", "danger")
        return redirect(url_for('admin_dashboard', admin_id=admin_id))
    
    # Update parking lot details
    if request.method == 'POST':
        new_price = request.form.get("price_per_hour")
        new_prime_location_name = request.form.get("prime_location_name")
        new_address = request.form.get("address")
        new_pin_code = request.form.get("pincode")
        #TODO: to update max_spots we require to create or delete some parking spots. Needs additional logic.
        # new_max_spots = request.form.get("max_spots")

        # Update the parking lot details
        parking_lot.price_per_hour = new_price
        parking_lot.prime_location_name = new_prime_location_name
        parking_lot.address = new_address
        parking_lot.pin_code = new_pin_code
        #TODO: Needed proper logic to update max_spots
        # parking_lot.max_spots = new_max_spots

        try:
            db.session.commit()
            flash("Parking lot details updated successfully!", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating parking lot details: {str(e)}", "danger")
        return redirect(url_for('view_parking_lot', admin_id=admin_id, lot_id=lot_id))
    
    return render_template("edit_parking_lot.html", parking_lot=parking_lot)



@app.route("/admin/<string:admin_id>/deleteLot/<string:lot_id>", methods=['POST'])
@login_required #TODO: change to `@admin_required`
def delete_parking_lot(admin_id, lot_id):
    """Delete functionality for parking lots. Possible only when all parking spots are empty."""
    if not current_user.is_admin or current_user.id != admin_id:
        flash("Admin permission required! Access denied.", 'danger')
        return redirect(url_for('login'))
    
    parking_lot = ParkingLot.query.options(joinedload(ParkingLot.spots)).filter_by(id=lot_id).first()

    if not parking_lot:
        flash("Parking lot not found.", "danger")
        return redirect(url_for('admin_dashboard', admin_id=admin_id))
    
    # If all spots are available, delete the parking lot and its spots
    if all(spot.status == 'A' for spot in parking_lot.spots):
        try:
            db.session.delete(parking_lot)
            db.session.commit()
            flash("Parking lot and its spots deleted successfully.", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"Error deleting parking lot: {str(e)}", "danger")
        return redirect(url_for('admin_dashboard', admin_id=admin_id))

    else:
        flash("Cannot delete lot: Some spots are occupied.", "danger")
        return redirect(url_for('admin_dashboard', admin_id=current_user.id))

    

# On parking spots no create and update is allowed, so only read and delete.
@app.route("/admin/<string:admin_id>/viewLot/<string:lot_id>/viewSpot/<string:spot_id>", methods=['GET'])
@login_required #TODO: change to `@admin_required`
def view_parking_spot(admin_id, lot_id, spot_id):
    if not current_user.is_admin or current_user.id != admin_id:
        flash("Admin permission required! Access denied.", 'danger')
        return redirect(url_for('login'))

    parking_lot = ParkingLot.query.filter_by(id=lot_id).first()
    if not parking_lot:
        flash("Parking lot not found.", "danger")
        return redirect(url_for('admin_dashboard', admin_id=admin_id))

    parking_spot = ParkingSpot.query.filter_by(id=spot_id, lot_id=lot_id).first()
    if not parking_spot:
        flash("Parking spot not found.", "danger")
        return redirect(url_for('view_parking_lot', admin_id=admin_id, lot_id=lot_id))

    return render_template("view_parking_spot.html", parking_lot=parking_lot, parking_spot=parking_spot)


@app.route("/admin/<string:admin_id>/viewLot/<string:lot_id>/deleteSpot/<string:spot_id>", methods=['POST'])
@login_required #TODO: change to `@admin_required`
def delete_parking_spot(admin_id, spot_id, lot_id):
    if not current_user.is_admin or current_user.id != admin_id:
        flash("Admin permission required! Access denied.", 'danger')
        return redirect(url_for('login'))

    parking_lot = ParkingLot.query.filter_by(id=lot_id).first()
    if not parking_lot:
        flash("Parking lot not found.", "danger")
        return redirect(url_for('admin_dashboard', admin_id=admin_id))

    parking_spot = ParkingSpot.query.filter_by(id=spot_id, lot_id=lot_id).first()
    if not parking_spot:
        flash("Parking spot not found.", "danger")
        return redirect(url_for('view_parking_lot', admin_id=admin_id, lot_id=lot_id))

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

    return redirect(url_for('view_parking_lot', admin_id=admin_id, lot_id=lot_id))


### User functionalities
@app.route("/user/<string:user_id>/dashboard")
@login_required
def user_dashboard(user_id):
    if current_user.is_admin or current_user.id != user_id:
        flash("You are an Admin.\nRequest Denied.", 'danger')
        return redirect(url_for('login'))
    return render_template("user_dashboard.html")



#TODO: Edit profile fuctionality for both Users and Admins
@app.route("/user/<string:id>/editprofile", methods=['GET','POST'], defaults={'is_admin': False} )
@app.route("/admin/<string:id>/editprofile", methods=['GET','POST'], defaults={'is_admin': True} )
@login_required
def editProfile(id, is_admin):
    if current_user.id == id:
        if request.method == "POST":
            user = User.query.filter_by(id=id).first()
            if (not is_admin and not user.is_admin) or (is_admin and user.is_admin):
                # Get form data
                full_name = request.form.get("full_name")
                email = request.form.get("email")
                username = request.form.get("username").strip()

                # unique username validation
                existing_user = User.query.filter_by(username=username).first()
                if existing_user and existing_user.id != id:
                    flash("Username already exists. Please choose a different one.", "danger")
                    return redirect(url_for('editProfile', id=id, is_admin=is_admin))
                
                # unique email validation
                existing_email = User.query.filter_by(email=email).first()
                if existing_email and existing_email.id != id:
                    flash("Email already exists. Please choose a different one.", "danger")
                    return redirect(url_for('editProfile', id=id, is_admin=is_admin))
                
                # If a new password is provided, hash it
                new_password = request.form.get("new_password")
                user.password = generate_password_hash(new_password) if new_password.strip() else user.password

                # Update user details
                user.full_name = full_name
                user.email = email
                user.username = username

                try:
                    db.session.commit()
                except Exception as e:
                    db.session.rollback()
                    flash(f"Error updating profile: {str(e)}", "danger")
                    return redirect(url_for('editProfile', id=id, is_admin=is_admin))
                
                flash("Profile updated successfully!", "success")
                return redirect(url_for('user_dashboard', user_id=id)) if not is_admin else redirect(url_for('admin_dashboard', admin_id=id))
            else:
                flash("Permission Denied", "danger")
                return redirect(url_for('login'))
            
        # Handle GET request
        return render_template('editProfile.html')
    else:
        flash("Permission Denied! Invalid User.", "danger")
        return redirect(url_for('login'))





@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "success")
    return redirect(url_for("index"))