from uuid import uuid4
from flask_login import UserMixin
from datetime import datetime
from shortuuid import uuid  # shotuuids are more human readable

from . import db

# User model
class User(db.Model, UserMixin):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4())) # using direct str(uuid.uuid4()) assigned same id to all
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    full_name = db.Column(db.String(80))
    password = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    is_flagged = db.Column(db.Boolean, default=False)

    reservations = db.relationship(
        'Reservation',
        backref='user',
        lazy=True,
        order_by="Reservation.parking_timestamp"
    )


# Parking Lot
class ParkingLot(db.Model):
    id = db.Column(db.String(22), primary_key=True, default=lambda: str(uuid()))  # using lambda function calls the function each time an instance is created
    prime_location_name = db.Column(db.String(100), nullable=False)
    price_per_hour = db.Column(db.Float, nullable=False)
    address = db.Column(db.String(255), nullable=False)
    pin_code = db.Column(db.String(10), nullable=False)
    max_spots = db.Column(db.Integer, nullable=False)

    uses = db.relationship(
        'Reservation', 
        backref='lot', 
        lazy=True,
        order_by="Reservation.parking_timestamp",
        overlaps="spot,reservations"
    )

    spots = db.relationship(
        'ParkingSpot', 
        backref='parent', 
        lazy=True,
        # Cascade ensures that if a parking lot is deleted 
        # all of its children spots will be deleted as well 
        cascade='all, delete-orphan'  
    )

    def total_occupied(self):
        """Returns the total number of occupied parking spots in the lot."""
        return ParkingSpot.query.filter_by(lot_id=self.id, status='O').count()
    
    def total_available(self):
        """Returns the total number of available parking spots in the lot."""
        return ParkingSpot.query.filter_by(lot_id=self.id, status='A').count()

    def total_revenue(self):
        """Calculates the total revenue generated from all finished reservations in this parking lot."""
        total_revenue = 0.0
        for spot in self.spots:
            for reservation in spot.reservations:
                if reservation.leaving_timestamp:
                    total_revenue += reservation.reservation_cost()

        return total_revenue

# Parking Spot
class ParkingSpot(db.Model):
    id = db.Column(db.Integer, nullable=False)
    lot_id = db.Column(db.String(22), db.ForeignKey('parking_lot.id'), nullable=False)
    status = db.Column(db.String(1), default='A')  # {"A": "Available", "O": "Occupied"}

    reservations = db.relationship(
        'Reservation', 
        backref='spot', 
        lazy=True, 
        order_by="Reservation.parking_timestamp",
        foreign_keys='Reservation.spot_id',
        overlaps="lot,uses"
    )  # Order by parking_timestamp to get a chronological ordering

    __table_args__ = (
        db.PrimaryKeyConstraint('id', 'lot_id', name='pk_composite_key'), # ref: "https://www.reddit.com/r/flask/comments/g3tje5/composite_key_for_flasksqlalchemy/"
    )

    def is_available(self) -> bool:
        return self.status == 'A'
    

# Reservation
class Reservation(db.Model):
    id = db.Column(db.String(22), primary_key=True, default=lambda: str(uuid()))
    status = db.Column(db.String(1), default='R') # {"R":"Reserved", "F":"Finished"} 

    lot_id = db.Column(db.String(22), db.ForeignKey('parking_lot.id'), nullable=False)
    spot_id = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.String(36), db.ForeignKey('user.id'), nullable=False)

    car_id = db.Column(db.String(10), unique=True, nullable=False)
    parking_timestamp = db.Column(db.DateTime, default=datetime.now)
    leaving_timestamp = db.Column(db.DateTime, nullable=True)

    __table_args__ = (
        db.ForeignKeyConstraint(
            ['lot_id', 'spot_id'], 
            ['parking_spot.lot_id', 'parking_spot.id'],
            name = 'fk_reservation_spot', # migrate gives `ValueError: Constraint must have a name`
            ondelete='CASCADE' # deletes reservation when a spot is deleted
        ),
    )

    def duration(self):
        end_time = self.leaving_timestamp or datetime.now()
        duration = (end_time - self.parking_timestamp).total_seconds() / 60 # duration in minutes
        return round(duration, 2)


    def reservation_cost(self):
        lot_price = self.lot.price_per_hour
        # duration = self.duration() / 60 # duration in hours 
        end_time = self.leaving_timestamp or datetime.now() # The time it leaves or the entire fare he booked the lot
        duration = (end_time - self.parking_timestamp).total_seconds() / 3600 # duration in hours
        return round(duration * lot_price, 2)
    
    
