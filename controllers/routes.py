from flask import render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app import app, db, login_manager
from models.models import User, ParkingLot, ParkingSpot, Reservation 

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


# every other routes will go here
@app.route("/admin/dashboard/<string:admin_id>")
@login_required
def admin_dashboard(admin_id):
    if not current_user.is_admin or current_user.id != admin_id:
        flash("Nope", 'info')
        return redirect(url_for('login'))
    return render_template("admin_dashboard.html", user=current_user)

@app.route("/user/dashboard/<string:user_id>")
@login_required
def user_dashboard(user_id):
    if current_user.is_admin or current_user.id != user_id:
        flash("Nope", 'info')
        return redirect(url_for('login'))
    return render_template("user_dashboard.html", user=current_user)



@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "success")
    return redirect(url_for("index"))