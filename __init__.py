from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from .config import Config

# Initialize extensions
db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()

# Configure the login manager
# 'login' is the function name of our login route
login_manager.login_view = 'main.login'
login_manager.login_message_category = 'info' # Optional: for styling flash messages

def create_app(config_class=Config):
    """Create and configure an instance of the Flask application."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Bind extensions to the app
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)

    # Import and register blueprints (our routes)
    # We import here to avoid circular dependencies
    from . import routes
    app.register_blueprint(routes.main_bp)

    with app.app_context():
        # This will create the database tables if they don't exist
        db.create_all()

    return app