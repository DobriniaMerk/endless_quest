from flask import Blueprint, redirect, render_template, url_for
from db import get_db

profile_bp = Blueprint("paragraph", __name__, url_prefix="/")

langs = ["ru", "en"]

@profile_bp.route("<lang>/<int:id>/profile", methods=["GET"])
def show(id : int, lang : str):
    if lang not in langs:
        return redirect(url_for("profile.show", id=id, lang=langs[0]))
    db = get_db()
    raw = db.get_user_profile(id, lang)
    exists = bool(raw)
    return render_template(
            'profile.html',
            variables=raw
            )
