from flask import Blueprint, redirect, render_template, request, url_for, session, make_response
import bleach
from werkzeug.datastructures import MultiDict
import json

from db import get_db
import parser

from .locale_data import locale

paragraph_bp = Blueprint("paragraph", __name__, url_prefix="/")

langs = ["ru", "en"]

# def new_paragraph(text: str) -> int:
#     """Generate a new paragraph ID not yet in use"""
#     db = get_db()
#     existing = []
#     connection = db.connection()
#     cursor = connection.cursor()
#     cursor.execute('SELECT id FROM paragraphs')
#     existing = [row['id'] for row in cursor.fetchall()]
#     maxparagr = int(db.get_variable('maxparagr', None) or 0)
#     connection.close()
#     new_id = randint(2, maxparagr)
#     while new_id in existing:
#         new_id = randint(2, maxparagr)
#     return new_id;


def clean(text: str) -> str:
    return bleach.clean(text, tags=[])


def setvars(reqargs: MultiDict[str, str], redirect_arg, username: str | None):
    if username:
      db = get_db()
      id = db.userid_by_name(username)
      if id is None:
          return

      for var, val in reqargs.items():
          db.set_variable(var, id, val)
    else:
        guest_vars = request.cookies.get('guest_vars')
        if guest_vars:
            variables = json.loads(guest_vars)
        else:
            variables = {}
        for var, val in reqargs.items():
            variables[var] = val
        resp = make_response(redirect(redirect_arg))
        resp.set_cookie('guest_vars', json.dumps(variables), max_age = 720*3600)
        return resp

@paragraph_bp.route("/", methods=["GET"])
def index():
    return redirect(url_for("paragraph.show", id=0, lang=langs[0]))


@paragraph_bp.route("<lang>/<int:id>", methods=["GET", "POST"])
def show(lang: str, id: int):
    if len(request.args) > 0:
        resp = setvars(request.args, f'{id}', session.get("username"))
        if resp:
            return resp

    if lang not in langs:
        return redirect(url_for("paragraph.show", id=id, lang=langs[0]))
    if request.method == "POST":
        return redirect(url_for("paragraph.show", id=request.form["id"], lang=lang))
    db = get_db()

    raw = db.get_paragraph(id, lang)
    exists = bool(raw)
    paragraph = {"id": id, "lang": lang, "title": "", "story": "", "protected": False}
    if not exists:
        paragraph["title"] = locale[lang]["show"]["not_written"]["title"]
        paragraph["story"] = locale[lang]["show"]["not_written"]["story"]
    # elif raw[f'current_{lang}'] is None:
    #     paragraph['title'] = locale[lang]['show']['translate']['title']
    #     paragraph['story'] = locale[lang]['show']['translate']['story']
    else:
        def variable_getter(key):
            if "username" in session.keys():
                user_id = db.userid_by_name(session["username"])
                val = db.get_variable(key, user_id)
                if val is None:
                    raise KeyError(f"Variable '{key}' not found")
                return val
            else:
                guest_vars = request.cookies.get('guest_vars')
                if guest_vars:
                    variables = json.loads(guest_vars)
                    if key in variables:
                        return variables[key]
                raise KeyError(f"Variable '{key}' not found")
        # paragraph['protected'] = bool(raw['protected'])
        paragraph["story"] = parser.process_page(raw[0], variable_getter)
        paragraph["title"] = raw[1]
    paragraph["rendered"] = paragraph["story"]
    return render_template(
        "paragraph/show.html",
        paragraph=paragraph,
        exists=exists,
        locale=locale[lang]
    )


@paragraph_bp.route("<lang>/<int:id>/edit", methods=["GET", "POST"])
def edit(lang: str, id: int):
    if lang not in langs:
        return redirect(url_for("paragraph.show", id=id, lang=langs[0]))
    db = get_db()
    if request.method == "POST":
        title = request.form["title"]
        story = request.form["story"]
        if not title:
            return redirect(url_for("paragraph.show", id=4096, lang=lang))
        edit_id = db.edit_paragraph(id, story, title, protected=False, lang=lang)
        return redirect(url_for("paragraph.show", id=id, lang=lang))
    raw = db.get_paragraph(id, lang)
    title = ""
    story = ""
    if raw:
        title = raw[1]
        story = raw[0]
    paragraph = {"id": id, "title": title, "story": story}
    return render_template(
        "paragraph/edit.html", paragraph=paragraph, ln=lang, locale=locale[lang]
    )


@paragraph_bp.route("/account", methods=["GET"])
def account():
    if "username" in session:
        username = session["username"]
        email = session.get("email", "не указано")
    else:
        username = "Гость"
        email = "не указано"
    return render_template("account.html",
                           username=username,
                           email=email,
                           locale=locale.get("ru"))
