from flask import Blueprint, render_template, session
from db import get_db

from .locale_data import locale

profile_bp = Blueprint("profile", __name__, url_prefix="/")

langs = ["ru", "en"]

@profile_bp.route("<lang>/<int:id>/profile", methods=["GET"])
def show(id : int, lang : str):
    db = get_db()
    raw = db.get_user_profile(db.userid_by_name(session["username"]))
    exists = bool(raw)
    print(raw)
    return render_template(
            'profile.html',
            variables=raw,
            paragraph={"lang": lang, "id": id},
            locale=locale.get(lang, locale["ru"])
            )
