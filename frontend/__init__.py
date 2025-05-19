from flask import Flask

from .auth import auth_bp
from .paragraph import paragraph_bp
from .moderation import moderation_bp
from .guest import guest_bp
from .profile import profile_bp


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
