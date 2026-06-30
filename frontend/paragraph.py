import json
from flask import (
    Blueprint,
    redirect,
    render_template,
    request,
    url_for,
    session,
    make_response,
)
import bleach
from werkzeug.datastructures import MultiDict
import requests

from db import get_db
import parser

from .locale_data import locale

paragraph_bp = Blueprint("paragraph", __name__, url_prefix="/")

langs = ["ru", "en"]


def clean(text: str) -> str:
    """
    Sanitize input text by escaping all HTML tags.

    Args:
        text (str): The input string to be cleaned.

    Returns:
        str: Cleaned string with HTML tags escaped.
    """
    return bleach.clean(text, tags=[])


def setvars(reqargs: MultiDict[str, str], redirect_arg, username: str | None):
    """
    Set user-specific or guest-specific variables based on request arguments.

    If the user is logged in, variables are stored in the database. Otherwise,
    they are stored in a cookie for guest access.

    Args:
        reqargs (MultiDict[str, str]): Dictionary of variable names and values from the request.
        redirect_arg (str): URL path or identifier to redirect to after setting variables.
        username (str | None): Username of the logged-in user, if any.

    Returns:
        Response | None: A Flask response object with updated cookies (for guests),
                         or None if variables are set for a logged-in user.
    """
    if username:
        db = get_db()
        userid = db.userid_by_name(username)
        if userid is None:
            return None

        for var, val in reqargs.items():
            db.set_variable(var, userid, val)
        return None

    guest_vars = request.cookies.get("guest_vars")

    if guest_vars:
        variables = json.loads(guest_vars)
    else:
        variables = {}

    for var, val in reqargs.items():
        variables[var] = val

    resp = make_response(redirect(redirect_arg))
    resp.set_cookie("guest_vars", json.dumps(variables), max_age=720 * 3600)
    return resp


def getvar(name: str) -> None|str:
    """
    Gets variable by name from current session either from database or cookies.

    Args:
        name (str): Name of the variable.

    Returns:
        str | None
    """
    username = session.get("username")
    if username:
        db = get_db()
        try:
            return db.get_variable(name, db.userid_by_name(username))
        except:
            return None
    else:
        try:
            return json.loads(request.cookies.get("guest_vars"))[name]
        except:
            return None


@paragraph_bp.route("/", methods=["GET"])
def index():
    """
    Redirect the root URL to the first paragraph with the default language.

    Returns:
        Response: A redirect response to the paragraph display route.
    """
    try:
        ind = int(getvar("currentParagraph"))
    except:
        ind = 0
    return redirect(url_for("paragraph.show", ind=ind, lang=langs[0]))


@paragraph_bp.route("<lang>/<int:ind>", methods=["GET"])
def show(lang: str, ind: int):
    """
    Display a specific paragraph by index and language.

    On GET: Renders the paragraph page, processing variables for dynamic content.

    Args:
        lang (str): Language code (e.g., 'en', 'ru').
        ind (int): Paragraph index.

    Returns:
        Response: Rendered HTML template or redirect response.
    """
    if lang not in langs:
        return redirect(url_for("paragraph.show", ind=ind, lang=langs[0]))

    db = get_db()
    raw = db.get_paragraph(ind, lang)
    exists = bool(raw)

    args = request.args.copy()
    if exists and getvar("currentParagraph") != str(ind):
        args.add("currentParagraph", str(ind))

    if len(args) > 0:
        resp = setvars(args, str(ind), session.get("username"))
        if resp:
            return resp

    paragraph = {"id": ind, "lang": lang, "title": "", "story": "", "protected": False}
    if not exists:
        paragraph["title"] = locale[lang]["show"]["not_written"]["title"]
        paragraph["story"] = locale[lang]["show"]["not_written"]["story"]
    else:

        def variable_getter(key):
            if "username" in session.keys():
                user_id = db.userid_by_name(session["username"])
                val = db.get_variable(key, user_id)
                if val is None:
                    raise KeyError(f"Variable '{key}' not found")
                return val

            guest_vars = request.cookies.get("guest_vars")
            if guest_vars:
                variables = json.loads(guest_vars)
                if key in variables:
                    return variables[key]
            raise KeyError(f"Variable '{key}' not found")

        paragraph["story"] = parser.process_page(raw[0], variable_getter)
        paragraph["title"] = raw[1]
    paragraph["rendered"] = paragraph["story"]
    return render_template(
        "paragraph/show.html", paragraph=paragraph, exists=exists, locale=locale[lang]
    )


@paragraph_bp.route("<lang>/<int:ind>/edit", methods=["GET", "POST"])
def edit(lang: str, ind: int):
    """
    Edit an existing paragraph identified by index and language.

    On GET: Displays the edit form populated with current paragraph data.
    On POST: Saves changes to the paragraph in the database.

    Args:
        lang (str): Language code (e.g., 'en', 'ru').
        ind (int): Paragraph index.

    Returns:
        Response: Rendered HTML template or redirect response.
    """
    if lang not in langs:
        return redirect(url_for("paragraph.show", ind=ind, lang=langs[0]))
    db = get_db()
    if request.method == "POST":
        title = request.form["title"]
        story = request.form["story"]
        if not title:
            return redirect(url_for("paragraph.show", ind=4096, lang=lang))
        db.edit_paragraph(ind, story, title, protected=False, lang=lang)
        return redirect(url_for("paragraph.show", ind=ind, lang=lang))
    raw = db.get_paragraph(ind, lang)
    title = ""
    story = ""
    if raw:
        title = raw[1]
        story = raw[0]
    paragraph = {"id": ind, "lang": lang, "title": title, "story": story}
    return render_template(
        "paragraph/edit.html", paragraph=paragraph, ln=lang, locale=locale[lang]
    )


@paragraph_bp.route("/account", methods=["GET"])
def account():
    """
    Display the account page with user info if logged in, or guest info otherwise.

    Returns:
        Response: Rendered HTML template for the account page.
    """
    if "username" in session:
        username = session["username"]
        email = session.get("email", "не указано")
    else:
        username = "Гость"
        email = "не указано"
    return render_template(
        "account.html", username=username, email=email, locale=locale.get("ru")
    )
