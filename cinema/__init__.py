import os

from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
import dotenv

class Base(DeclarativeBase):
  pass

db = SQLAlchemy(model_class=Base)

def create_app(test_config=None):
    app = Flask(__name__)

    dotenv.load_dotenv()

    # A secret for signing session cookies
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")

    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("SQLALCHEMY_DATABASE_URI")
    db.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = "auth.login"
    login_manager.init_app(app)
    from . import model

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(model.User, int(user_id))

    # Register blueprints
    # (we import main from here to avoid circular imports in the next lab)
    from . import main
    from . import auth

    app.register_blueprint(main.bp)
    app.register_blueprint(auth.bp)
    return app
