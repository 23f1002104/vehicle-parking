from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, login_user, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from Models.models import User
from Models.models import db
from . import auth_bp


#? auth.py 

### Authentication Functionalities
@auth_bp.route("/register", methods=['GET','POST'])
def register():
    if request.method == "POST":
        username = request.form.get("username").strip() # strip to ensure no extra space
        # unique username validation
        user = User.query.filter_by(username=username).first()
        if user:
            flash("Username already exists! Choose another username", "secondary")
            return redirect(url_for('auth_bp.register'))
        
        # unique email validation
        email = request.form.get("email")
        user = User.query.filter_by(email=email).first()
        if user:
            flash("Account already exist with this mail. Kindly login to proceed furthur", "secondary")
            return redirect(url_for('auth_bp.login'))
        
        pwd = request.form.get("password")
        password = generate_password_hash(pwd)
        full_name = request.form.get("full_name")

        new_user = User(username=username, email=email, password=password, full_name=full_name)
        db.session.add(new_user)
        db.session.commit()
        flash("Registration successful!", "success")
        return redirect(url_for('auth_bp.login'))
    
    return render_template('auth/register.html')


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for("admin_bp.admin_dashboard", admin_id = current_user.id))
        else:
            return redirect(url_for("user_bp.user_dashboard", user_id = current_user.id))
    if request.method == "POST":
        username = request.form.get("username").strip()
        password = request.form.get("password")
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            flash("Login successful!", "success")
            if user.is_admin:
                return redirect(url_for("admin_bp.admin_dashboard", admin_id = user.id))
            else:
                return redirect(url_for("user_bp.user_dashboard", user_id = user.id))
        else:
            flash("Invalid credentials", "danger")
            return redirect(url_for('auth_bp.login'))

    return render_template('auth/login.html')




@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "success")
    return redirect(url_for('main_bp.index'))
