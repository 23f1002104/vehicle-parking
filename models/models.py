import uuid
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
# from app import db
db = SQLAlchemy()

# User model
class User(db.Model, UserMixin):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4())) # using direct str(uuid.uuid4()) assigned same id to all and caused trouble
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    is_flagged = db.Column(db.Boolean, default=False)

    reservations = db.relationship('Reservation', backref='user', lazy=True)



# Parking Lot
class ParkingLot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    prime_location_name = db.Column(db.String(100), nullable=False)
    price_per_unit_time = db.Column(db.Float, nullable=False)
    address = db.Column(db.String(255), nullable=False)
    pin_code = db.Column(db.String(10), nullable=False)
    max_spots = db.Column(db.Integer, nullable=False)

    spots = db.relationship('ParkingSpot', backref='lot', lazy=True)


# Parking Spot
class ParkingSpot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    lot_id = db.Column(db.Integer, db.ForeignKey('parking_lot.id'), nullable=False)
    status = db.Column(db.String(1), default='A')  # A: Available, O: Occupied

    reservations = db.relationship('Reservation', backref='spot', lazy=True)


# Reservation
class Reservation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    spot_id = db.Column(db.Integer, db.ForeignKey('parking_spot.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    parking_timestamp = db.Column(db.DateTime, default=datetime.now())
    leaving_timestamp = db.Column(db.DateTime, nullable=True)

    def calculate_cost(self):
        lot_price = self.spot.lot.price_per_unit_time
        end_time = self.leaving_timestamp or datetime.now() # The time it leaves or the entire fare he booked the lot
        duration = (end_time - self.parking_timestamp).total_seconds() / 3600
        return round(duration * lot_price, 2)

