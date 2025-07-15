from flask import Flask
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect

from config import Config
from Models import db


app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
csrf = CSRFProtect(app)


# configure flask login
login_manager = LoginManager()
login_manager.login_view = "auth_bp.login"
login_manager.login_message = "Please log in to access this page."
login_manager.login_message_category = "danger"
login_manager.init_app(app)


# import it at the end to avoid circular import issue
from Controllers import main_bp, auth_bp, admin_bp, user_bp

app.register_blueprint(main_bp)
csrf.exempt(main_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)
csrf.exempt(admin_bp)
app.register_blueprint(user_bp)


from Models.models import User, ParkingLot, ParkingSpot, Reservation
# if put inside __name__ == "__main__" it will not work with `flask run`
with app.app_context():
    db.create_all()
    if not User.query.filter_by(is_admin=True).all():
        from create_admin import create_admin
        create_admin()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

if __name__ == "__main__":
    app.run(debug=True)