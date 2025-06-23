from app import app
from Models.models import User, db
from werkzeug.security import generate_password_hash

def create_admin():
    with app.app_context():
    # Customize the admin data
        admin1 = User(
            username='admin1',
            email='admin1@example.com',
            password=generate_password_hash('myAdminPass'),  # if you're hashing
            is_admin=True
        )
        admin2 = User(
            username='admin2',
            email='admin2@example.com',
            password=generate_password_hash('myAdminPass'),  # if you're hashing
            is_admin=True
        )
        admin3 = User(
            username='admin3',
            email='admin3@example.com',
            password=generate_password_hash('myAdminPass'),  # if you're hashing
            is_admin=True
        )
        try:
            db.session.add_all([admin1, admin2, admin3])
            db.session.commit()
            print("Admin users created successfully.")
        except Exception as e:
            db.session.rollback()
            print(f"Error creating admin user: {e}")
            return
        return
    
if __name__ == "__main__":
    create_admin()