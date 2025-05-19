from flask import Blueprint, redirect, render_template, request, url_for, session, make_response
from db import get_db

moderation_bp = Blueprint("moderation", __name__, url_prefix="/")

@moderation_bp.route("/<lang>/<int:id>/history", methods=["GET", "POST"])
def history(lang: str, id: int):
    db = get_db()
    if request.method == "GET":
        versions = [db.get_paragraph(id, lang, i) for i in range(10)]
        versions = [(x[0], x[1], i) for i, x in enumerate(versions) if x is not None]
        name = session.get("username")
        can_revert = False
        if name is not None and db.is_moderator(name):
            can_revert = True;
        return render_template("history.html", versions=versions, lang=lang, id=id, can_revert=can_revert)
    try:
        db.revert_paragraph(id, lang, int(request.args["revision"]))
    except:
        redirect(url_for("moderation.history", lang=lang, id=id))
    return redirect(url_for("paragraph.show", lang=lang, id=id))
