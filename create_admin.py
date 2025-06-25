from app import app
from Models.models import User, db
from werkzeug.security import generate_password_hash

def create_admin():
    with app.app_context():
    # Customize the admin data
        admin = User(
            username='admin',
            full_name = "SuperUser", 
            email='admin@example.com',
            password=generate_password_hash('myadmin'),  # if you're hashing
            is_admin=True
        )
        try:
            db.session.add(admin)
            db.session.commit()
            print("Admin users created successfully.")
        except Exception as e:
            db.session.rollback()
            print(f"Error creating admin user: {e}")
            return
        return
    
if __name__ == "__main__":
    create_admin()