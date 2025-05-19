import sqlite3
from typing import Optional, Tuple
from pathlib import Path
from werkzeug.security import generate_password_hash, check_password_hash
from flask import current_app


class DB:
    """A simple SQLite database interface for managing users, variables, and paragraphs."""

    def __init__(self, db_path: str, schema_path: str) -> None:
        """
        Initialize the database handler.

        Args:
            db_path (str): Path to the SQLite database file.
            schema_path (Optional[str]): Path to the SQL schema file. If None, assumes 'schema.sql' in the same directory.
        """
        self.db_path = db_path
        if schema_path:
            self.schema_path = Path(schema_path)
        else:
            self.schema_path = Path(__file__).parent / "schema.sql"
        self._init_db()

    def _init_db(self) -> None:
        """
        Initialize the database by applying the SQL schema if the database is uninitialized.
        This method executes the SQL script located at self.schema_path.
        """
        schema_file = self.schema_path
        if not schema_file.is_file():
            raise FileNotFoundError(f"Schema file not found: {schema_file}")
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='variables'"
            )
            if cur.fetchone():
                return
            script = schema_file.read_text(encoding="utf-8")
            conn.executescript(script)

    def _connect(self) -> sqlite3.Connection:
        """
        Establish a new SQLite database connection.

        Returns:
            sqlite3.Connection: A connection object to the SQLite database.
        """
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def get_variable(self, name: str, user_id: int) -> Optional[str]:
        """
        Retrieve the value of a user-specific variable.

        Args:
            name (str): The name of the variable.
            user_id (int): The user's ID.

        Returns:
            Optional[str]: The value of the variable, or None if not found.
        """
        connection = self._connect()
        cursor = connection.cursor()
        cursor.execute(
            "SELECT value FROM variables WHERE name = ? AND user_id = ?",
            (name, user_id),
        )
        result = cursor.fetchone()
        connection.close()
        return result["value"] if result else None

    def set_variable(
        self, name: str, user_id: int, value: str, visible: bool = False
    ) -> None:
        """
        Set or update the value of a user-specific variable.

        Args:
            name (str): The name of the variable.
            user_id (int): The user's ID.
            value (str): The new value to store.
        """
        connection = self._connect()
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO variables (name, user_id, visible, value) VALUES (?, ?, ?, ?)" # DO NOT PLACE A COMMA HERE, THIS IS INTENDED
            "ON CONFLICT (name, user_id) DO UPDATE SET value = excluded.value",
            (name, user_id, visible, value),
        )
        connection.commit()
        connection.close()

    def get_paragraph(
        self, paragraph_id: int, lang: str = "ru", back_history: int = 0
    ) -> Optional[Tuple[str, str]]:
        """
        Retrieve the text of a paragraph in the specified language.

        Args:
            paragraph_id (int): The ID of the paragraph.
            lang (str, optional): The language ('ru' or 'en'). Defaults to 'ru'.
            back_history (int, optional): How much edits back to get paragraph. 0 is current version.

        Returns:
            Optional[Tuple[str, str]]: The paragraph text and title, or None if not found.
        """
        connection = self._connect()
        cursor = connection.cursor()
        column = "current_ru" if lang == "ru" else "current_en"
        cursor.execute(f"SELECT {column} FROM paragraphs WHERE id = ?", (paragraph_id,))
        row = cursor.fetchone()
        if not row or not row[column]:
            connection.close()
            return None
        id = row[column]
        story_row = None
        for _ in range(back_history + 1):
            cursor.execute("SELECT story, title, previous FROM edits WHERE id = ?", (id,))
            story_row = cursor.fetchone()
            if story_row is None:
                break
            id = story_row["previous"]
        connection.close()
        return (story_row["story"], story_row["title"]) if story_row else None

    def get_user_profile(self, user_id : int) -> list[sqlite3.Row]:
        """
        Get all variables for a given user by his id

        Args:
            user_id (int): User ID

        Returns:
            list[sqlite3.Row]: List of set variables. Names are at ["name"], values are at ["value"]
        """
        connection = self._connect()
        cursor = connection.cursor()
        cursor.execute(f"SELECT name, value FROM variables WHERE user_id = ?", (user_id,))
        row = cursor.fetchall()
        connection.close()
        return row if row else []

    def edit_paragraph(
        self,
        paragraph_id: int,
        new_text: str,
        new_title: str,
        protected: bool = False,
        lang: str = "ru",
    ) -> int:
        """
        Edit or create a paragraph, storing a new version in the history.

        Args:
            paragraph_id (int): The ID of the paragraph.
            new_text (str): The new content of the paragraph.
            new_title (str): The new title of paragraph.
            protected (bool, optional): Whether the paragraph is protected. Defaults to False.
            lang (str, optional): The language ('ru' or 'en'). Defaults to 'ru'.

        Returns:
            int: The ID of the new edit entry.
        """
        connection = self._connect()
        cursor = connection.cursor()
        column = "current_ru" if lang == "ru" else "current_en"
        cursor.execute(
            "SELECT id, protected, current_ru, current_en FROM paragraphs WHERE id = ?",
            (paragraph_id,),
        )
        existing = cursor.fetchone()
        previous_edit = None
        if existing:
            previous_edit = existing[column]
        else:
            cursor.execute(
                "INSERT INTO paragraphs(id, protected) VALUES (?, ?)",
                (paragraph_id, int(protected)),
            )
        cursor.execute(
            "INSERT INTO edits(paragraph, lang, previous, story, title) VALUES (?, ?, ?, ?, ?)",
            (paragraph_id, lang, previous_edit, new_text, new_title),
        )
        new_edit_id = cursor.lastrowid
        cursor.execute(
            f"UPDATE paragraphs SET {column} = ?, protected = ? WHERE id = ?",
            (new_edit_id, int(protected), paragraph_id),
        )
        connection.commit()
        connection.close()
        return new_edit_id


    def revert_paragraph(self, paragraph_id: int, lang: str, back_history: int) -> None:
        """
        Revert paragraph to what it was back_history edits ago. Does nothing is history contains less edits.

        Args:
            paragraph_id (int): The ID of the paragraph.
            lang (str): The language ('ru' or 'en').
            back_history (int): How much edits to revert.
        """
        contents = self.get_paragraph(paragraph_id, lang, back_history)
        if contents is None:
            return
        self.edit_paragraph(paragraph_id, contents[0], contents[1], False, lang)


    def add_user(
        self, username: str, email: str, password: str, is_moderator: bool = False
    ) -> int:
        """
        Create a new user account.

        Args:
            username (str): The username.
            email (str): The user's email.
            password (str): The plain-text password.
            is_moderator (bool, optional): Whether the user is a moderator. Defaults to False.

        Returns:
            int: The ID of the newly created user.
        """
        password_hash = generate_password_hash(password)
        connection = self._connect()
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO users(username, email, password_hash, is_moderator) VALUES (?, ?, ?, ?)",
            (username, email, password_hash, int(is_moderator)),
        )
        user_id = cursor.lastrowid
        connection.commit()
        connection.close()
        return user_id

    def find_user(self, username: str, password: str) -> Optional[Tuple[int, bool]]:
        """
        Authenticate a user with the provided credentials.

        Args:
            username (str): The username.
            password (str): The plain-text password.

        Returns:
            Optional[Tuple[int, bool]]: A tuple of (user_id, is_moderator) if found, else None.
        """
        connection = self._connect()
        cursor = connection.cursor()
        cursor.execute(
            "SELECT id, password_hash, is_moderator FROM users WHERE username = ?",
            (username,)
        )
        row = cursor.fetchone()
        connection.close()
        if row and check_password_hash(row["password_hash"], password):
            return (row["id"], bool(row["is_moderator"]))
        return None

    def is_moderator(self, username: str) -> Optional[bool]:
        """
        Check if user has rights for moderation

        Args:
            username (str): The username.

        Returns Optional[bool]: True if user is a moderator. None if user is not found.
        """
        connection = self._connect()
        cursor = connection.cursor()
        cursor.execute(
            "SELECT is_moderator FROM users WHERE username = ?",
            (username,)
        )
        row = cursor.fetchone()
        connection.close()
        return bool(row["is_moderator"]) if row is not None else None

    def userid_by_name(self, username: str) -> Optional[int]:
        """
        Get user id by a name.

        Args:
            username (str): The username.

        Returns:
            Optional[int]: User id if found, else None.
        """
        connection = self._connect()
        cursor = connection.cursor()
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
        return row["id"] if row else None

_db = None


def get_db() -> DB:
    global _db
    if _db is None:
        _db = DB(
            current_app.config["DATABASE_PATH"], current_app.config["SCHEMA_PATH"]
        )
    return _db

def clear_db() -> None:
    global _db
    _db = None
