from flask import render_template, redirect, url_for, request, flash, abort
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
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
            for _ in range(max_spots):
                new_spot = ParkingSpot(lot_id=new_lot.id)
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



@app.route("/admin/<string:admin_id>/viewLot/<string:lot_id>")
@login_required #TODO: change to `@admin_required`
def view_parking_lot(admin_id, lot_id):
    if not current_user.is_admin or current_user.id != admin_id:
        flash("Admin permission required! Access denied.", 'danger')
        return redirect(url_for('login'))
    parking_lot = ParkingLot.query.get(lot_id)
    if not parking_lot:
        flash("Parking lot not found.", "danger")
        return redirect(url_for('admin_dashboard', admin_id=admin_id))
    return render_template("view_parking_lot.html", parking_lot=parking_lot)


### User functionalities
@app.route("/user/<string:user_id>/dashboard")
@login_required
def user_dashboard(user_id):
    if current_user.is_admin or current_user.id != user_id:
        flash("You are an Admin.\nRequest Denied.", 'danger')
        return redirect(url_for('login'))
    return render_template("user_dashboard.html")



#TODO: Edit profile fuctionality for both Users and Admins
@app.route("/user/<string:id>/edit", methods=['GET','POST'], defaults={'is_admin': False} )
@app.route("/admin/<string:id>/edit", methods=['GET','POST'], defaults={'is_admin': True} )
@login_required
def edit(id, is_admin):
    if current_user.id == id:
        if request.method == "GET":
            return render_template('editProfile.html')
        else:
            user = User.query.filter_by(id=id).first()
        if not is_admin and not user.is_admin:
            pass
        if is_admin and user.is_admin:
            pass
    else:
        abort(403)
    pass



@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "success")
    return redirect(url_for("index"))