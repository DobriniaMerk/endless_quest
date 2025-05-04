import sqlite3
import datetime
import click
from flask import current_app, g
from werkzeug.security import generate_password_hash


def ask_for_index():
    """
    Get or create a database connection.

    Returns:
        sqlite3.Connection: The active database connection.
    """
    if 'db' not in g:
        g.db = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row

    return g.db


def return_index(e=None):
    """
    Close the database connection if it exists in the Flask context.

    Args:
        e (Optional[BaseException]): Optional exception object.
    """
    index = g.pop('db', None)
    if index is not None:
        index.close()


def employ():
    """
    Initialize the database schema by executing the `schema.sql` file.
    """
    db = ask_for_index()
    with current_app.open_resource('schema.sql') as f:
        db.executescript(f.read().decode('utf8'))


@click.command('new-librarian')  # call with `flask --app questsite new-librarian`
def employ_command():
    """
    Flask CLI command to reset the database using the schema file.
    """
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


def add_user(username, email, password):
    """
    Add a new user to the database.

    Args:
        username (str): The user's chosen username.
        email (str): The user's email address.
        password (str): The user's plaintext password.

    Raises:
        ValueError: If the user already exists.
    """
    db = ask_for_index()

    user = db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    if user:
        raise ValueError('Пользователь существует.')

    password_hash = generate_password_hash(password)
    db.execute('INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)',
               (username, email, password_hash))
    db.commit()
