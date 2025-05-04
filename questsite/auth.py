from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    request,
    session,
    current_app,
)

from werkzeug.security import generate_password_hash, check_password_hash

from .db import DB

langs = ["ru", "en"]

auth_bp = Blueprint("auth", __name__, url_prefix="/")

_db = None


def get_db() -> DB:
    global _db
    if _db is None:
        _db = DB(
            current_app.config["DATABASE_PATH"], current_app.config.get("SCHEMA_PATH")
        )
    return _db


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    """
    Handles user registration.

    GET: Renders the registration form.
    POST: Validates and saves the new user to the database,
          starts session on success.

    Returns:
        Union[str, Response]: HTML page or redirect to the first paragraph.
    """
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        db = get_db()
        if db.user_exists(username):
            flash("Имя пользователя уже существует")
            return redirect(url_for("auth.register"))
        
        password_hash = generate_password_hash(password)

        db.add_user(username, email, password_hash)
        session["username"] = username
        return redirect(url_for("paragraph.show", id=0, lang=langs[0]))
    return render_template("register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """
    Handles user login.

    GET: Renders the login form.
    POST: Authenticates the user and starts a session.

    Returns:
        Union[str, Response]: Renders the login form or redirects to the start page if login is successful.
    """

    if "username" in session:
        return redirect(url_for("paragraph.show", id=0, lang=langs[0]))
    if request.method == "POST":
        db = get_db()
        user = db.find_user(request.form["username"], request.form["password"])
        if user:
            session["username"] = request.form["username"]
            return redirect(url_for("paragraph.show", id=0, lang=langs[0]))
        flash("Неправильное имя пользователя или пароль")
    return render_template("login.html")


@auth_bp.route("/logout")
def logout():
    """
    Logs the user out by clearing the session.

    Returns:
        Response: Redirects to the login page.
    """
    session.clear()
    flash("Вы вышли из системы.", "info")
    return redirect(url_for("auth.login"))
