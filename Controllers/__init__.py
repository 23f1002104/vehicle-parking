# Distributed into admin.py, user.py, auth.py and main.py
# to avoid circular import issues
from flask import Blueprint


main_bp = Blueprint('main_bp', __name__, url_prefix='/')
from . import main  # Attach main routes to the blueprint 

auth_bp = Blueprint('auth_bp', __name__, url_prefix='/auth')
from . import auth  # Attach auth routes to the blueprint

admin_bp = Blueprint('admin_bp', __name__, url_prefix='/admin')
from . import admin  # Attach admin routes to the blueprint

user_bp = Blueprint('user_bp', __name__, url_prefix='/user')
from . import user  # Attach user routes to the blueprint
