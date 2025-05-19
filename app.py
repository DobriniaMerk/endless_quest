import os
from typing import Optional
from flask import Flask
from frontend import register_blueprints

def create_app(test_config: Optional[dict]=None):
    """
    Creates flask app

    Args:
        test_config (Optional[dict]): App config for tests.
    """
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

    register_blueprints(app)

    return app
