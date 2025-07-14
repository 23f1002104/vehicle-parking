from os import abort
from flask import render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from sqlalchemy.orm import joinedload  # To eager load from database
from Forms.misc_forms import ReservationForm
from app import db, csrf
from Models.models import User, ParkingLot, ParkingSpot, Reservation
from . import user_bp



from collections import defaultdict # easier to work with

def get_lot_summary(user_id):
    # Get all finished reservations for the user
    reservations = Reservation.query.filter_by(user_id=user_id).filter(Reservation.status == 'F').all()

    # lot_id → { 'lot': lot_obj, 'total_cost': X, 'total_duration': Y }
    lot_summary = defaultdict(lambda: {'lot': None, 'total_cost': 0.0, 'total_duration': 0.0})

    for res in reservations:
        lot_id = res.lot_id
        cost = res.reservation_cost()
        duration_seconds = res.duration(arg=True)  # total seconds

        lot_summary[lot_id]['lot'] = res.lot
        lot_summary[lot_id]['total_cost'] += cost
        lot_summary[lot_id]['total_duration'] += duration_seconds

    # Optional: format duration to hh:mm:ss
    for data in lot_summary.values():
        total_seconds = int(data['total_duration'])
        hrs, rem = divmod(total_seconds, 3600)
        mins, secs = divmod(rem, 60)
        data['formatted_duration'] = f"{hrs:02}h {mins:02}m {secs:02}s"

    return lot_summary




from functools import wraps
# user_required decorator to ensure that the user is logged in and is not an admin
# ref: "https://github.com/sayan01/bootcamp-july/blob/master/routes.py"
def user_required(f):
    @wraps(f)
    @login_required # available via flask_login directly
    def func(*args, **kwargs):
        
        if current_user.is_admin:
            flash("User required! Access denied.", 'danger')
            return redirect(url_for('auth_bp.login')) # abort(403)
        
        if kwargs.get("user_id") != current_user.id:
            flash("Unauthorized access", 'danger')
            return redirect(url_for('auth_bp.login')) # abort(403)   
        
        return f(*args, **kwargs)
    return func

### User functionalities

@user_bp.route("/<string:user_id>/dashboard")
@user_required
@csrf.exempt
def user_dashboard(user_id):
    user = User.query.filter_by(id=user_id, is_admin=False).first_or_404()
    reservations = Reservation.query.filter_by(user_id=user_id).order_by(
        Reservation.status == 'F',
        Reservation.parking_timestamp.desc()
    ).limit(5).all()
    # print(reservations)
    return render_template("users/user_dashboard.html", reservations=reservations)



@user_bp.route("/<string:user_id>/editprofile", methods=['GET','POST'])
@user_required
@csrf.exempt
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


#TODO: Add user summary
@user_bp.route("/<string:user_id>/summary", methods=['GET'])
@user_required
@csrf.exempt
def user_summary(user_id):
    user = User.query.filter_by(id=user_id).first_or_404()
    reservations = Reservation.query.filter_by(user_id=user_id).order_by(
        Reservation.status == 'F',
        Reservation.parking_timestamp.desc()
    ).all()

    lot_summary = get_lot_summary(user_id)

    return render_template("users/user_summary.html", user=user, reservations=reservations, lot_summary=lot_summary)


@user_bp.route("/<string:user_id>/search", methods=['GET'])
@user_required
@csrf.exempt
def search(user_id):
    from rapidfuzz import fuzz, utils
    query = request.args.get("query", "").strip()
    field = request.args.get("field", "").strip() or "prime_location_name"  # Default search field

    if not query:
        return render_template("users/user_search.html", results=["No query passed"], query=query, field=field, user_id=user_id)

    processed_query = utils.default_process(query)
    threshold = 85 # needs to be adjusted for better results
    results = []
    
    if fuzz.WRatio(query.lower(), "available", processor=utils.default_process, score_cutoff=90) > 90:
        results = [spot for spot in ParkingSpot.query.filter_by(staus="A").all()]

    # ParkingLot Search
    if field in ("parking_lot", "prime_location_name"):
        for lot in ParkingLot.query.all():
            for col in lot.__table__.columns:
                value = str(getattr(lot, col.name))
                score = fuzz.WRatio(processed_query, value, processor=utils.default_process, score_cutoff=threshold)
                print(value, score, col.name)
                if score > threshold:
                    results.append(lot)
                    break # move to next item

    # Reservation Search
    elif field == "reservations":
        # use eager load as reservation has foreign keys to user and parking_spot
        for reservation in Reservation.query.options(
            joinedload(Reservation.user),
            joinedload(Reservation.spot)
        ).all():
            for col in reservation.__table__.columns:
                value = str(getattr(reservation, col.name))
                score = fuzz.WRatio(processed_query, value, processor=utils.default_process, score_cutoff=threshold)
                print(value ,score, col.name)
                if score > threshold:
                    results.append(reservation)
                    break # move to next item

    else:
        flash("Invalid search field", "secondary")

    # Deduplicate by object ID
    results_list = list({getattr(obj, 'id'): obj for obj in results}.values())
    # final result
    results = results_list if len(results_list) > 0 else ["Try using better query or field. Could not find a match"]
    print(results, type(query), field) # Debugging
    return render_template("users/user_search.html", results=results, query=query, field=field, user_id=user_id)
    

@user_bp.route("/<string:user_id>/viewlots", methods=['GET'])
@user_required
@csrf.exempt
def view_parking_lots(user_id):
    lots = ParkingLot.query.all()
    return render_template("users/view_parking_lots.html", lots=lots)




@user_bp.route("/<string:user_id>/<string:lot_id>/reservespot", methods=['GET','POST'])
@user_required
def reserve_spot(user_id,lot_id):
    if current_user.id == user_id:
        lot = ParkingLot.query.filter_by(id=lot_id).first_or_404() # return 404 error if not found
        spot = ParkingSpot.query.filter_by(lot_id=lot_id, status="A").first_or_404() # checks if any spot is available in that lot

        form = ReservationForm()

        if form.validate_on_submit():
            res_username = form.username.data
            res_user_id = User.query.filter_by(username=res_username).first().id
            res_lot_id = form.lot_id.data
            res_spot_id = spot.id
            res_car_id = form.car_id.data.strip()
            _ = form.prime_loc_name.data

            assert res_username == current_user.username
            assert res_lot_id == lot.id

            try:
                new_reservation = Reservation(
                    lot_id = res_lot_id,
                    spot_id = res_spot_id,
                    user_id = res_user_id,
                    car_id = res_car_id
                )
                db.session.add(new_reservation)
                spot.status = "O"
                db.session.commit()
                flash("Reservation Successful!", "success")
                    
            except Exception as e:
                db.session.rollback()
                flash(f"Reservation failed!\nError:{e}", "danger")
                
            finally:
                return redirect(url_for("user_bp.user_dashboard", user_id=current_user.id))


            
            # if request.method == 'POST':
            #     res_username = request.form.get("username")
            #     res_user_id = User.query.filter_by(username=res_username).first().id
            #     res_lot_id = request.form.get("lot_id")
            #     res_spot_id = spot.id
            #     res_car_id = request.form.get("car_id").strip()
            #     try:
            #         new_reservation = Reservation(
            #             lot_id = res_lot_id,
            #             spot_id = res_spot_id,
            #             user_id = res_user_id,
            #             car_id = res_car_id
            #         )
            #         db.session.add(new_reservation)
            #         spot.status = "O"
            #         db.session.commit()
            #         flash("Reservation Successful!", "success")
                    
            #     except Exception as e:
            #         db.session.rollback()
            #         flash(f"Reservation failed!\nError:{e}", "danger")
                
            #     finally:
            #         return redirect(url_for("user_bp.user_dashboard", user_id=current_user.id))
                
        print(lot, spot.status)
        return render_template('users/reserve_spot.html', lot=lot, spot=spot, form=form)
    
    else:
        abort(403)

@user_bp.route("/<string:user_id>/<string:lot_id>/clearspot/<string:res_id>", methods=['GET','POST'])
@user_required
@csrf.exempt
def release_spot(user_id, lot_id, res_id):
    reservation = Reservation.query.filter_by(id=res_id, user_id=user_id, lot_id=lot_id).order_by(Reservation.parking_timestamp.desc()).first_or_404()
    if request.method == "POST":
        if reservation.status == "R": # Ongoing reservation
            if current_user.id == user_id:
                try:
                    from datetime import datetime
                    reservation.leaving_timestamp = datetime.now()
                    db.session.flush()
                    total_fare = reservation.reservation_cost()
                    flash(f"Spot released! Fare: {total_fare}", "success")
                    reservation.status = "F"
                    spot = ParkingSpot.query.filter_by(id=reservation.spot_id, lot_id=reservation.lot_id).first()
                    spot.status = "A"
                    db.session.commit()
                except Exception as e:
                    db.session.rollback()
                    print(str(e))
                    flash(f"Spot release failed!\nError:{e}", "danger")
                finally:
                    return redirect(url_for("user_bp.user_dashboard", user_id=current_user.id))
            else:
                abort(403)
        else:
            flash("No ongoing reservation found", "secondary")
            return redirect(url_for("user_bp.user_dashboard", user_id=current_user.id))

    return render_template("users/release_spot.html", reservation=reservation)