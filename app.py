from flask import Flask
from flask_login import LoginManager
# from flask_migrate import migrate # when need to change in database
from config import Config
from Models.models import db


app = Flask(__name__)
app.config.from_object(Config)


db.init_app(app)
# migrate = migrate(app,db)

# configure flask login
login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.login_message = "Please log in to access this page."
login_manager.login_message_category = "danger"
login_manager.init_app(app)


# import it at the end to avoid circular import issue
import Controllers.routes
from Models.models import User, ParkingLot, ParkingSpot, Reservation


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)