import re
from random import randint
from flask import Blueprint, redirect, render_template, request, url_for, session, make_response
import bleach
from werkzeug.datastructures import MultiDict
import json

from db import get_db
import parser

bp = Blueprint("paragraph", __name__, url_prefix="/")

langs = ["ru", "en"]

@bp.route("<lang>/<int:id>/profile", methods=["GET"])
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
