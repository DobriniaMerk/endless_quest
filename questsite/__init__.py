import os
from flask import Flask


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='theverysecretkeynooneshouldknow',
        DATABASE=os.path.join(app.instance_path, 'database.sqlite')
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_envvar('ENDLESSQUEST_SETTINGS')
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

    return app
