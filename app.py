from flask import Flask
from flask_login import LoginManager
from config import Config
from Models.models import db


app = Flask(__name__)
app.config.from_object(Config)


db.init_app(app)


# configure flask login
login_manager = LoginManager()
login_manager.login_view = "auth_bp.login"
login_manager.login_message = "Please log in to access this page."
login_manager.login_message_category = "danger"
login_manager.init_app(app)


# import it at the end to avoid circular import issue
from Controllers import main_bp, auth_bp, admin_bp, user_bp
from Models.models import User, ParkingLot, ParkingSpot, Reservation


app.register_blueprint(main_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(user_bp)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

# if put inside __name__ == "__main__" it will not work with `flask run`
with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)