from flask import (
    Blueprint,
    redirect,
    render_template,
    request,
    url_for,
    session,
)
from db import get_db
from .paragraph import locale

moderation_bp = Blueprint("moderation", __name__, url_prefix="/")


@moderation_bp.route("/<lang>/<int:ind>/history", methods=["GET", "POST"])
def history(lang: str, ind: int):
    """
    Handle viewing and reverting paragraph revision history.

    On GET:
        - Retrieves up to 10 historical versions of a paragraph.
        - Renders the 'history.html' template with version data and
          current paragraph info.
        - Determines whether the current user (if logged in) can revert
          based on moderator status.

    On POST:
        - Attempts to revert the paragraph to a specific revision index
          based on the 'revision' request argument.
        - Redirects back to the history view regardless of success.

    Args:
        lang (str): Language code for the paragraph (e.g., 'en', 'ru').
        id (int): The unique identifier for the paragraph.

    Returns:
        Response: Rendered HTML template for GET, or redirect for POST.
    """
    db = get_db()
    if request.method == "GET":
        versions = [db.get_paragraph(ind, lang, i) for i in range(10)]
        versions = [(x[0], x[1], i) for i, x in enumerate(versions) if x is not None]
        name = session.get("username")
        can_revert = False
        if name is not None and db.is_moderator(name):
            can_revert = True

        raw = db.get_paragraph(ind, lang)
        paragraph = {
            "id": ind,
            "lang": lang,
            "title": "",
            "story": "",
            "protected": False,
        }
        if raw:
            paragraph["story"] = raw[0]
            paragraph["title"] = raw[1]
        return render_template(
            "history.html",
            versions=versions,
            lang=lang,
            id=ind,
            can_revert=can_revert,
            locale=locale[lang],
            paragraph=paragraph,
        )

    try:
        db.revert_paragraph(ind, lang, int(request.args["revision"]))
    except KeyError:
        return redirect(url_for("moderation.history", lang=lang, id=ind))
    return redirect(url_for("moderation.history", lang=lang, id=ind))
