from flask import Flask
from .auth import *
from .paragraph import *
from .moderation import *
from .guest import *

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
