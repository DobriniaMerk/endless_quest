import sqlite3
import datetime
import click
from flask import current_app, g


def ask_for_index():
    if 'db' not in g:
        g.db = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row

    return g.db


def return_index(e=None):
    index = g.pop('db', None)
    if index is not None:
        index.close()


def employ():
    db = ask_for_index()

    with current_app.open_resource('schema.sql') as f:
        db.executescript(f.read().decode('utf8'))


@click.command('new-librarian')  # call with `flask --app questsite new-librarian`
def employ_command():
    sure = click.confirm('Are you sure you want to start library anew? Old books will persist only in Shadows.')
    if not sure:
        return

    click.echo("Leaving Shadow image at: " + current_app.config['DATABASE'] + '.' + datetime.datetime.now().strftime('%Y_%m_%d') + '.bak')

    db = ask_for_index()
    db.backup(sqlite3.connect(current_app.config['DATABASE'] + '.' + datetime.datetime.now().strftime('%Y_%m_%d') + '.bak'))

    click.echo("Creating library at: " + current_app.config['DATABASE'])

    employ()
    click.echo('Librarian ready.')


def onstart(app):
    app.teardown_appcontext(return_index)
    app.cli.add_command(employ_command)
