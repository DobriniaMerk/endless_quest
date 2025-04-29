import re
from random import randint
from questsite import librarian
from flask import Blueprint, redirect, render_template, request, url_for
from markdown import markdown
import bleach

bp = Blueprint('paragraph', __name__, url_prefix='/')

langs = ['ru', 'en']

locale = {
    'ru': {
        'show': {
            'not_written': {
                'title': '???',
                'story': 'События с этого момента покрываются туманом, и решительно ничего нельзя разобрать.'
            },
            'translate': {
                'title': '???',
                'story': 'Что было дальше никто не знает, но люди знающие утверждают что такое уже происходило, \
                только тогда все было по-английски и никто ничего не понял. Если вы переводчик, можете объяснить тем, кто не столь сведущ.'
            },
            'edit': 'Изменить',
            'add': 'Добавить',
            'goto': 'Перейти',
        },
        'edit': {
            'page-title': 'Новая страница',
            'title': 'Заголовок',
            'story': 'Разворот',
            'save': 'Опубликовать',
            'cancel': 'Выбросить черновик',
        }
    },
    'en': {
        'show': {
            'not_written': {
                'title': '???',
                'story': 'The story from this point is uncertain. Decide the outcome yourself, if you dare.'
            },
            'translate': {
                'title': '???',
                'story': 'What happened next is unclear, but those who have the knowledge of Russian can transfer the truth from over the Edge.'
            },
            'edit': 'Edit',
            'add': 'Add',
            'goto': 'Goto',
        },
        'edit': {
            'page-title': 'Write new page',
            'title': 'Title',
            'story': 'Story',
            'save': 'Publish',
            'cancel': 'Better not',
        }
    }
}


def new_paragraph():
    db = librarian.ask_for_index()
    ids = []
    for row in db.execute('SELECT id FROM paragraphs').fetchall():
        ids.append(row['id'])
    maxparagr = int(db.execute("SELECT * FROM general WHERE name = 'maxparagr'").fetchone()['value'])

    new_id = randint(2, maxparagr)
    while (new_id in ids):
        new_id = randint(2, maxparagr)
    return new_id


def clean(text):
    return bleach.clean(text, tags=[])


def escape(text):
    # BEWARE: regex black magic
    # It escapes all links that contain anything aside numbers
    return re.sub(r'\[([^]]+)\]\(([^)]*[^\d)][^)]*)\)', r'\[\1\]\(\2\)', text)


def fill_links(text):
    def fill(match):
        return f'[{match.group(1)}]({new_paragraph()})'

    def parenth(match):
        print('MATCHED!!!!')
        return f'[{match.group(1)}]()'

    text = re.sub(r'\[([^]\n]+)\](?!\()', parenth, text)  # [...] -> [...]()
    return re.sub(r'\[([^]\n]+)\]\(\)', fill, text)  # [...]() -> [...](№)


@bp.route('/', methods=['GET'])
def index():
    return redirect(url_for('paragraph.show', id=0, lang=langs[0]))


@bp.route('<lang>/<int:id>', methods=['GET', 'POST'])
def show(lang, id):
    if lang not in langs:
        return redirect(url_for('paragraph.show', id=id, lang=langs[0]))

    if request.method == 'POST':
        return redirect(url_for('paragraph.show', id=request.form['id'], lang=lang))

    db = librarian.ask_for_index()
    raw = db.execute('SELECT * FROM paragraphs WHERE id = ?', (id,)).fetchone()
    e = True

    paragraph = {
        'id': id,
        'lang': lang,
        'title': '',
        'story': '',
        'protected': False
    }

    if raw is None:
        paragraph['title'] = locale[lang]['show']['not_written']['title']
        paragraph['story'] = locale[lang]['show']['not_written']['story']
        e = False
    elif raw['current_' + lang] is None:
        paragraph['title'] = locale[lang]['show']['translate']['title']
        paragraph['story'] = locale[lang]['show']['translate']['story']
    else:
        paragraph['protected'] = raw['protected']  # intended before rewriting `raw`

        raw = db.execute('SELECT * FROM edits WHERE id = ?', (raw['current_' + lang],)).fetchone()
        paragraph['title'] = raw['title']
        paragraph['story'] = raw['story']


    paragraph['rendered'] = markdown(escape(paragraph['story']), extensions=['nl2br'])
    return render_template('paragraph/show.html', paragraph=paragraph, exists=e, locale=locale[lang]['show'])


@bp.route('<lang>/<int:id>/edit', methods=('GET', 'POST'))
def edit(lang, id):
    if lang not in langs:
        return redirect(url_for('paragraph.show', id=id, lang=langs[0]))

    if request.method == 'POST':
        title = clean(request.form['title'])
        story = fill_links(clean(request.form['story']))

        if not title:
            return redirect(url_for('paragraph.show', id=4096, lang=lang))

        db = librarian.ask_for_index()
        paragraph = db.execute('SELECT * FROM paragraphs WHERE id = ?', (id,)).fetchone()

        if paragraph is None:
            paragraph = db.execute('INSERT INTO paragraphs (id) VALUES (?) RETURNING *', (id,)).fetchone()

        index = db.execute('''INSERT INTO edits (paragraph, lang, type, previous, title, story)
                      VALUES (?, ?, ?, ?, ?, ?) RETURNING id''', (
                          id,
                          lang,
                          'new' if paragraph['current_' + lang] is None else 'edit',
                          paragraph['current_' + lang],
                          title,
                          story
                      )).fetchone()[0]
        db.execute(f'UPDATE paragraphs SET current_{lang} = ? WHERE id = ?', (index, id))

        db.commit()

        return redirect(url_for('paragraph.show', id=id, lang=lang))

    db = librarian.ask_for_index()

    raw = db.execute('SELECT * FROM paragraphs WHERE id = ?', (id,)).fetchone()
    paragraph = {
        'id': id,
        'title': '',
        'story': ''
    }
    if raw is not None and raw['current_' + lang] is not None:
        raw = db.execute('SELECT * FROM edits WHERE id = ?', (raw['current_' + lang],)).fetchone()

        paragraph['title'] = raw['title']
        paragraph['story'] = raw['story']

    return render_template('paragraph/edit.html', paragraph=paragraph, ln=lang, locale=locale[lang]['edit'])
