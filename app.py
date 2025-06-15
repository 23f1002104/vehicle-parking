from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate



app = Flask(__name__)
app.config.from_object(Config)

db = SQLAlchemy(app)
migrate = Migrate(app,db)




from controllers import routes

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)