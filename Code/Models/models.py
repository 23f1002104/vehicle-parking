from uuid import uuid4
from flask_login import UserMixin
from datetime import datetime
from shortuuid import uuid  # shotuuids are more human readable

from . import db

# User model
class User(db.Model, UserMixin):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    username = db.Column(db.String(36), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    full_name = db.Column(db.String(80))
    password = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

    reservations = db.relationship(
        'Reservation',
        back_populates='user',
        lazy=True,
        order_by='Reservation.parking_timestamp'
    )

    def total_reservations(self):
        return len(self.reservations)

    def total_expenses(self):
        return sum(r.reservation_cost() for r in self.reservations)


# Parking Lot
class ParkingLot(db.Model):
    id = db.Column(db.String(22), primary_key=True, default=lambda: str(uuid()))
    prime_location_name = db.Column(db.String(100), nullable=False)
    price_per_hour = db.Column(db.Float, nullable=False)
    address = db.Column(db.String(255), nullable=False)
    pin_code = db.Column(db.String(10), nullable=False)
    max_spots = db.Column(db.Integer, nullable=False)

    spots = db.relationship(
        'ParkingSpot',
        back_populates='lot',
        lazy=True,
        cascade='all, delete-orphan',
        passive_deletes=True
    )

    reservations = db.relationship(
        'Reservation',
        back_populates='lot',
        lazy=True,
        order_by="Reservation.parking_timestamp",
        overlaps="spot,reservations"
    )

    def update_max_spots(self, new_max_spots: int) -> bool:
        current_max = self.max_spots
        if new_max_spots == current_max:
            return True
        elif new_max_spots > current_max:
            for i in range(current_max + 1, new_max_spots + 1):
                db.session.add(ParkingSpot(id=i, lot_id=self.id, status='A'))
            self.max_spots = new_max_spots
            return True
        else:
            to_remove = current_max - new_max_spots
            removable = ParkingSpot.query.filter_by(lot_id=self.id, status='A').order_by(ParkingSpot.id.desc()).limit(to_remove).all()
            if len(removable) < to_remove:
                return False
            for s in removable:
                db.session.delete(s)
            self.max_spots = new_max_spots
            return True

    def total_occupied(self):
        return ParkingSpot.query.filter_by(lot_id=self.id, status='O').count()

    def total_available(self):
        return ParkingSpot.query.filter_by(lot_id=self.id, status='A').count()

    def total_revenue(self):
        tot = 0.0
            
        for spot in self.spots:
            for r in spot.reservations:
                if r.leaving_timestamp:
                    tot+= r.reservation_cost()

        return tot
        



# Parking Spot
class ParkingSpot(db.Model):
    id = db.Column(db.Integer, nullable=False)
    lot_id = db.Column(db.String(22), db.ForeignKey('parking_lot.id', ondelete='CASCADE'), nullable=False)
    status = db.Column(db.String(1), default='A')  # A = Available, O = Occupied

    __table_args__ = (
        db.PrimaryKeyConstraint('id', 'lot_id', name='pk_composite_key'),
    )

    lot = db.relationship('ParkingLot', back_populates='spots')

    reservations = db.relationship(
        'Reservation',
        back_populates='spot',
        lazy=True,
        order_by="Reservation.parking_timestamp",
        primaryjoin="and_(ParkingSpot.id == Reservation.spot_id, ParkingSpot.lot_id == Reservation.lot_id)"
    )

    def is_available(self):
        return self.status == 'A'


# Reservation
class Reservation(db.Model):
    id = db.Column(db.String(22), primary_key=True, default=lambda: str(uuid()))
    status = db.Column(db.String(1), default='R')  # R = Reserved, F = Finished

    lot_id = db.Column(db.String(22), db.ForeignKey('parking_lot.id', ondelete='CASCADE'), nullable=False)
    spot_id = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.String(36), db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    car_id = db.Column(db.String(10), nullable=False)  # Removed unique=True
    parking_timestamp = db.Column(db.DateTime, default=datetime.now)
    leaving_timestamp = db.Column(db.DateTime, nullable=True)

    __table_args__ = (
        db.ForeignKeyConstraint(
            ['lot_id', 'spot_id'],
            ['parking_spot.lot_id', 'parking_spot.id'],
            ondelete='CASCADE'
        ),
    )

    lot = db.relationship('ParkingLot', back_populates='reservations')
    spot = db.relationship('ParkingSpot', back_populates='reservations',
        primaryjoin="and_(Reservation.spot_id == ParkingSpot.id, Reservation.lot_id == ParkingSpot.lot_id)"
    )
    user = db.relationship('User', back_populates='reservations')

    def duration(self, arg=False):
        end_time = self.leaving_timestamp or datetime.now()
        duration = (end_time - self.parking_timestamp).total_seconds()
        hrs, rem = divmod(duration, 3600)
        mins, secs = divmod(rem, 60)
        return f"{int(hrs):02}h {int(mins):02}m {int(secs):02}s" if not arg else duration

    def reservation_cost(self):
        lot_price = self.lot.price_per_hour
        duration = self.duration(arg=True) / 3600  # hours
        return round(duration * lot_price, 0)

    
    
