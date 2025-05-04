import sqlite3
import hashlib
from typing import Optional, Any, Tuple

class DB:
    """A simple SQLite database interface for managing users, variables, and paragraphs."""
    def __init__(self, db_path : str) -> None:
        """
        Initialize the database handler.

        Args:
            db_path (str): Path to the SQLite database file.
        """
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        """
        Initialize the database schema if needed.
        (Currently a placeholder; extend as necessary.)
        """
        pass

    def _connect(self) -> sqlite3.Connection:
        """
        Establish a new SQLite database connection.

        Returns:
            sqlite3.Connection: A connection object to the SQLite database.
        """
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def get_variable(self, name : str, user_id : int) -> Optional[str]:
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

    def set_variable(self, name : str, user_id : int, value : str, visible : bool = False) -> None:
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
            "INSERT INTO variables (name, user_id, visible, value) VALUES (?, ?, ?, ?)",
                "ON CONFLICT (name, user_id) DO UPDATE SET value = excluded.value",
            (name, user_id, visible, value)
        )
        connection.commit()
        connection.close()

    def get_paragraph(self, paragraph_id : int, lang : str = "ru") -> Optional[str]:
        """
        Retrieve the text of a paragraph in the specified language.

        Args:
            paragraph_id (int): The ID of the paragraph.
            lang (str, optional): The language ('ru' or 'en'). Defaults to 'ru'.

        Returns:
            Optional[str]: The paragraph text, or None if not found.
        """
        connection = self._connect()
        cursor = connection.cursor()
        column = "current_ru" if lang == "ru" else "current_en"
        cursor.execute(
            f"SELECT {column} FROM paragraphs WHERE id = ?",
            (paragraph_id,)
        )
        row = cursor.fetchone()
        if not row or not row[column]:
            connection.close()
            return None
        cursor.execute("SELECT story FROM edits WHERE id = ?", (paragraph_id,))
        story_row = cursor.fetchone()
        connection.close()
        return story_row['story'] if story_row else None


    def edit_paragrath(self, paragraph_id : int, new_text : str, protected : bool = False, lang : str = "ru") -> int:
        """
        Edit or create a paragraph, storing a new version in the history.

        Args:
            paragraph_id (int): The ID of the paragraph.
            new_text (str): The new content of the paragraph.
            protected (bool, optional): Whether the paragraph is protected. Defaults to False.
            lang (str, optional): The language ('ru' or 'en'). Defaults to 'ru'.

        Returns:
            int: The ID of the new edit entry.
        """
        connection = self._connect()
        cursor = connection.cursor()
        column = 'current_ru' if lang == 'ru' else 'current_en'
        cursor.execute(
            "SELECT id, protected, current_ru, current_en FROM paragraphs WHERE id = ?",
            (paragraph_id,)
        )
        existing = cursor.fetchone()
        previous_edit = None
        if existing:
            previous_edit = existing[column]
        else:
            cursor.execute(
                "INSERT INTO paragraphs(id, protected) VALUES (?, ?)",
                (paragraph_id, int(protected))
            )
        cursor.execute(
            "INSERT INTO edits(paragraph, lang, previous, story) VALUES (?, ?, ?, ?)",
            (paragraph_id, lang, previous_edit, new_text)
        )
        new_edit_id = cursor.lastrowid
        cursor.execute(
            f"UPDATE paragraphs SET {column} = ?, protected = ? WHERE id = ?",
            (new_edit_id, int(protected), paragraph_id)
        )
        connection.commit()
        connection.close()
        return new_edit_id

    def add_user(self, username : str, email : str, password : str, is_moderator : bool = False) -> int:
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
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        connection = self._connect()
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO users(username, email, password, is_moderator) VALUES (?, ?, ?, ?)",
            (username, email, password_hash, int(is_moderator))
        )
        user_id = cursor.lastrowid
        connection.commit()
        connection.close()
        return user_id

    def find_user(self, username : str, password : str) -> Optional[Tuple[int, bool]]:
        """
        Authenticate a user with the provided credentials.

        Args:
            username (str): The username.
            password (str): The plain-text password.

        Returns:
            Optional[Tuple[int, bool]]: A tuple of (user_id, is_moderator) if found, else None.
        """
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        connection = self._connect()
        cursor = connection.cursor()
        cursor.execute(
            "SELECT id, is_moderator FROM users WHERE username = ? AND password_hash = ?",
            (username, password_hash)
        )
        row = cursor.fetchone()
        connection.close()
        return (row['id'], bool(row['is_moderator'])) if row else None