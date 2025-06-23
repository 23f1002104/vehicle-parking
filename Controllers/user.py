from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import joinedload  # To eager load from database
from app import db
from Models.models import User, ParkingLot, ParkingSpot, Reservation
from . import user_bp

from functools import wraps
# user_required decorator to ensure that the user is logged in and is not an admin
# ref: "https://github.com/sayan01/bootcamp-july/blob/master/routes.py"
def user_required(f):
    @wraps(f)
    @login_required # available via flask_login directly
    def func(*args, **kwargs):
        if current_user.is_admin:
            flash("User required! Access denied.", 'danger')
            return redirect(url_for('auth_bp.login'))
        return f(*args, **kwargs)
    return func

### User functionalities

#? user.py
@user_bp.route("/<string:user_id>/dashboard")
@user_required
def user_dashboard(user_id):
    if current_user.is_admin or current_user.id != user_id:
        flash("You are an Admin.\nRequest Denied.", 'danger')
        return redirect(url_for('auth_bp.login'))
    return render_template("users/user_dashboard.html")

@user_bp.route("/<string:user_id>/editprofile", methods=['GET','POST'])
@user_required
def edit_user_profile(user_id):
    if current_user.id == user_id:
        if request.method == "POST":
            user = User.query.filter_by(id=user_id).first()
            if not user.is_admin or current_user.is_admin:
                # Get form data
                full_name = request.form.get("full_name")
                email = request.form.get("email")
                username = request.form.get("username").strip()

                # unique username validation
                existing_user = User.query.filter_by(username=username).first()
                if existing_user and existing_user.id != user_id:
                    flash("Username already exists. Please choose a different one.", "danger")
                    return redirect(url_for('user_bp.edit_user_profile', user_id=user_id))

                # unique email validation
                existing_email = User.query.filter_by(email=email).first()
                if existing_email and existing_email.id != user_id:
                    flash("Email invalid. Please choose a different one.", "danger")
                    return redirect(url_for('user_bp.edit_user_profile', user_id=user_id))

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
                    return redirect(url_for('user_bp.edit_user_profile', user_id=user_id))

                flash("Profile updated successfully!", "success")
                return redirect(url_for('user_bp.user_dashboard', user_id=user_id))
            else:
                flash("Permission Denied", "danger")
                return redirect(url_for('auth_bp.login'))

        # Handle GET request
        return render_template('users/edit_user_profile.html')
    else:
        flash("Permission Denied! Invalid User.", "danger")
        return redirect(url_for('auth_bp.login'))