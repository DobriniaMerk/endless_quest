import re
from random import randint
from flask import Blueprint, redirect, render_template, request, url_for, current_app, session
from markdown import markdown
import bleach
from werkzeug.datastructures import MultiDict

from .db import DB
from . import parser

bp = Blueprint("paragraph", __name__, url_prefix="/")

langs = ["ru", "en"]

locale = {
    "ru": {
        "show": {
            "not_written": {
                "title": "???",
                "story": "События с этого момента покрываются туманом, и решительно ничего нельзя разобрать.",
            },
            "translate": {
                "title": "???",
                "story": "Что было дальше никто не знает, но люди знающие утверждают что такое уже происходило, "
                "только тогда все было по-английски и никто ничего не понял. Если вы переводчик, "
                "можете объяснить тем, кто не столь сведущ.",
            },
            "edit": "Изменить",
            "add": "Добавить",
            "goto": "Перейти",
        },
        "edit": {
            "page-title": "Новая страница",
            "title": "Заголовок",
            "story": "Разворот",
            "save": "Опубликовать",
            "cancel": "Выбросить черновик",
        },
    },
    "en": {
        "show": {
            "not_written": {
                "title": "???",
                "story": "The story from this point is uncertain. Decide the outcome yourself, if you dare.",
            },
            "translate": {
                "title": "???",
                "story": "What happened next is unclear, but those who have the knowledge of Russian can transfer "
                "the truth from over the Edge.",
            },
            "edit": "Edit",
            "add": "Add",
            "goto": "Goto",
        },
        "edit": {
            "page-title": "Write new page",
            "title": "Title",
            "story": "Story",
            "save": "Publish",
            "cancel": "Better not",
        },
    },
}

_db = None


def get_db() -> DB:
    global _db
    if _db is None:
        _db = DB(
            current_app.config["DATABASE_PATH"], current_app.config.get("SCHEMA_PATH")
        )
    return _db


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


def setvars(reqargs: MultiDict[str, str], username: str):
    db = get_db()
    id = db.userid_by_name(username)
    if id is None:
        return

    for var, val in reqargs.items():
        db.set_variable(var, id, val)


@bp.route("/", methods=["GET"])
def index():
    return redirect(url_for("paragraph.show", id=0, lang=langs[0]))


@bp.route("<lang>/<int:id>", methods=["GET", "POST"])
def show(lang: str, id: int):
    setvars(request.args, session["username"])

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
        # paragraph['protected'] = bool(raw['protected'])
        paragraph["story"] = parser.process_page(raw[0], db.userid_by_name(session["username"]))
        paragraph["title"] = raw[1]
    paragraph["rendered"] = paragraph["story"]
    return render_template(
        "paragraph/show.html",
        paragraph=paragraph,
        exists=exists,
        locale=locale[lang]["show"],
    )


@bp.route("<lang>/<int:id>/edit", methods=["GET", "POST"])
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
        "paragraph/edit.html", paragraph=paragraph, ln=lang, locale=locale[lang]["edit"]
    )
