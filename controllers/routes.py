from flask import render_template, redirect, url_for, request, flash
from app import app, db
from models.models import User, ParkingLot, ParkingSpot, Reservation
# from flask import current_app as app  



@app.route("/")
def index():
    return render_template("index.html")

