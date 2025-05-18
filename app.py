import os
from flask import Flask, session
from frontend import auth_bp, bp

def create_app(test_config=None):
    app = Flask(__name__)

    if test_config is not None:
        app.config.from_mapping(test_config)
    else:
        app.config.from_mapping(
            SECRET_KEY="theverysecretkeynooneshouldknow",
            DATABASE_PATH=os.path.join(app.instance_path, "database.sqlite"),
            GRAMMAR_PATH=os.path.join(app.root_path, "parser/grammar.lark"),
            SCHEMA_PATH=os.path.join(app.root_path, "db/schema.sql")
        )

    os.makedirs(app.instance_path, exist_ok=True)

    @app.route("/lorem")
    def test():
        return "Lorem ipsum dolor sit amet"

    app.register_blueprint(bp)
    app.register_blueprint(auth_bp)

    return app
