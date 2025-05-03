import os
from flask import Flask, session
from .models import db, User
from flask_login import LoginManager, current_user
from .auth import auth_bp


login_manager = LoginManager()
login_manager.login_view = 'auth.login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)

    app.config.from_mapping(
        SECRET_KEY='theverysecretkeynooneshouldknow',
        SQLALCHEMY_DATABASE_URI='sqlite:///' + os.path.join(app.instance_path, 'database.sqlite'),
        DATABASE=os.path.join(app.instance_path, 'database.sqlite')
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        #app.config.from_envvar('ENDLESSQUEST_SETTINGS')
        pass
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    @app.route('/lorem')
    def test():
        return 'Lorem ipsum dolor sit amet'

    from . import librarian
    librarian.onstart(app)

    from . import paragraph
    app.register_blueprint(paragraph.bp)

    app.register_blueprint(auth_bp)

    db.init_app(app)
    login_manager.init_app(app)

    return app
