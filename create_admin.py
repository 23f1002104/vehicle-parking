from app import app
from Models.models import ParkingLot, ParkingSpot, User, db
from werkzeug.security import generate_password_hash

def create_admin():
    with app.app_context():
    # Customize the admin data
        admin = User(
            username='myadmin',
            full_name = "SuperUser", 
            email='admin@vpark.com',
            password=generate_password_hash('myadmin@vpark'),
            is_admin=True
        )
        try:
            db.session.add(admin)
            db.session.commit()
            print("Admin users created successfully.")
        except Exception as e:
            db.session.rollback()
            print(f"Error creating admin user: {e}")
        finally:
            db.session.close()
            return
        
def create_parking_lots():
    new_lot = ParkingLot(
        prime_location_name="prime_location_name",
        price_per_hour=100.0,
        address="test_address",
        pin_code=12345,
        max_spots=10
    )
    try:
        db.session.add(new_lot)
        db.session.flush()
        print("Parking Lot created successfully.")
        try:
            for num in range(new_lot.max_spots):
                new_spot = ParkingSpot(lot_id=new_lot.id, id=num+1)
                db.session.add(new_spot)
            db.session.commit()
            print("Parking Spots created successfully.")
        except Exception as e:  
            db.session.rollback()
            print(f"Error creating Parking Spots: {e}")
            return
    except Exception as e:
        db.session.rollback()
        print(f"Error creating Parking Lot: {e}")
    finally:
        db.session.close()
        return
    
def cerate_users():
    user1 = User(
        username='myuser1',
        full_name = "User", 
        email='user1@vpark.com',
        password=generate_password_hash('myuser1@vpark'),
        is_admin=False
    )
    user2 = User(
        username='myuser2',
        full_name = "User", 
        email='user2@vpark.com',
        password=generate_password_hash('myuser2@vpark'),
        is_admin=False
    )
    try:
        db.session.add(user1)
        db.session.add(user2)
        db.session.commit()
        print("Admin users created successfully.")
    except Exception as e:
        db.session.rollback()
        print(f"Error creating admin user: {e}")
        print(e.description)
    finally:
        db.session.close()
        return
    


def prepopulate_test_data():
    create_admin()
    create_parking_lots()
    cerate_users()