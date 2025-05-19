import os
from flask import Flask, request, session
from frontend import auth_bp, bp
from frontend.guest import guest_bp

from frontend.paragraph import locale as paragraph_locale, langs

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

    # @app.before_request
    # def save_last_page():
    #   if 'user_id' in session:
    #       page = request.path + ( '?' + request.query_string.decode() if request.query_string else '' )
    #       db = get_db()
    #       db.execute('REPLACE INTO user_sessions(user_id,last_page) VALUES(?,?)',
    #                   (session['user_id'], page))
    #       db.commit()

    register_blueprints(app)

    return app
