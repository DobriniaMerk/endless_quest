import os
from flask import Flask, session
from frontend import auth_bp, bp
from frontend.guest import guest_bp

def create_app(test_config=None):
    app = Flask(__name__)

    app.config.from_mapping(
        SECRET_KEY="theverysecretkeynooneshouldknow",
        DATABASE_PATH=os.path.join(app.instance_path, "database.sqlite"),
        GRAMMAR_PATH=os.path.join(app.root_path, "parser/grammar.lark"),
    )

    os.makedirs(app.instance_path, exist_ok=True)

    # if test_config is None:
    #     # load the instance config, if it exists, when not testing
    #     app.config.from_envvar("ENDLESSQUEST_SETTINGS")
    # else:
    #     # load the test config if passed in
    #     app.config.from_mapping(test_config)

    @app.route("/lorem")
    def test():
        return "Lorem ipsum dolor sit amet"

    @app.before_request
    def save_last_page():
      if 'user_id' in session:
          page = request.path + ( '?' + request.query_string.decode() if request.query_string else '' )
          db = get_db()
          db.execute('REPLACE INTO user_sessions(user_id,last_page) VALUES(?,?)',
                      (session['user_id'], page))
          db.commit()

    app.register_blueprint(bp)
    app.register_blueprint(auth_bp)

    return app
