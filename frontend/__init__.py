from flask import Flask

from frontend import profile
from .auth import *
from .paragraph import *
from .moderation import *
from .guest import *
from .profile import *

def register_blueprints(app: Flask) -> None:
    """
    Register all frontend blueprints in provided app

    Args:
        app (Flask): The app.
    """
    app.register_blueprint(auth_bp)
    app.register_blueprint(paragraph_bp)
    app.register_blueprint(moderation_bp)
    app.register_blueprint(guest_bp)
    app.register_blueprint(profile_bp)
