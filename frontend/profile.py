from flask import Blueprint, redirect, render_template, url_for
from db import get_db

from .locale_data import locale

profile_bp = Blueprint("profile", __name__, url_prefix="/")

langs = ["ru", "en"]

@profile_bp.route("<lang>/<int:id>/profile", methods=["GET"])
def show(id : int, lang : str):
    db = get_db()
    raw = db.get_user_profile(id, lang)
    exists = bool(raw)
    return render_template(
            'profile.html',
            variables=raw,
            paragraph={"lang": lang, "id": id},
            locale=locale.get(lang, locale["ru"])
            )
