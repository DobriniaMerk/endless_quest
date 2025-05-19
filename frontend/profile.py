from flask import Blueprint, render_template, session
from db import get_db

from .locale_data import locale

profile_bp = Blueprint("profile", __name__, url_prefix="/")

langs = ["ru", "en"]


@profile_bp.route("<lang>/<int:ind>/profile", methods=["GET"])
def show(ind: int, lang: str):
    """
    Display the profile page for the currently logged-in user.

    Retrieves user profile data from the database using the username stored
    in the session. Passes the data to the 'profile.html' template along with
    paragraph context and localized strings.

    Args:
        ind (int): Paragraph index to provide context (because… reasons).
        lang (str): Language code for localization (e.g., 'ru', 'en').

    Returns:
        Response: Rendered HTML template for the user's profile.
    """
    username = session.get("username")
    raw = []
    if username:
        db = get_db()
        raw = db.get_user_profile(db.userid_by_name(username))

    return render_template(
        "profile.html",
        variables=raw,
        paragraph={"lang": lang, "id": ind},
        locale=locale.get(lang, locale["ru"]),
    )
