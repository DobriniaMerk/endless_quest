import unittest
from app import create_app
import os
import tempfile
from db import get_db, clear_db


class AuthTestCase(unittest.TestCase):
    def setUp(self):
        # Создание временной БД
        self.db_fd, self.db_path = tempfile.mkstemp()
        self.app = create_app(
            {
                "TESTING": True,
                "DATABASE_PATH": self.db_path,
                "SECRET_KEY": "test",
                "SCHEMA_PATH": "db/schema.sql",
            }
        )
        self.ctx = self.app.app_context()
        self.ctx.push()
        self.client = self.app.test_client()

        clear_db()
        _db = get_db()
        _db.add_user("testuser", "test@example.com", "12345")

    def tearDown(self):
        self.ctx.pop()
        os.close(self.db_fd)
        os.unlink(self.db_path)

    def test_register(self):
        self.client.post(
            "/register",
            data={
                "username": "newuser",
                "email": "new@example.com",
                "password": "pass123",
            },
            follow_redirects=True,
        )

        response = self.client.get(
            "/account",
            follow_redirects=True,
        )

        self.assertIn("newuser", response.data.decode("utf-8"))

    def test_register_duplicate(self):
        response = self.client.post(
            "/register",
            data={
                "username": "testuser",
                "email": "another@example.com",
                "password": "pass456",
            },
            follow_redirects=True,
        )

        self.assertIn("Имя пользователя уже существует", response.data.decode("utf-8"))

    def test_login_success(self):
        self.client.post(
            "/login",
            data={"username": "testuser", "password": "12345"},
            follow_redirects=True,
        )

        response = self.client.get(
            "/account",
            follow_redirects=True,
        )

        self.assertIn("testuser", response.data.decode("utf-8"))

    def test_login_wrong_password(self):
        response = self.client.post(
            "/login",
            data={"username": "testuser", "password": "wrongpassword"},
            follow_redirects=True,
        )

        self.assertIn(
            "Неправильное имя пользователя или пароль", response.data.decode("utf-8")
        )

    def test_logout(self):
        self.client.post("/login", data={"username": "testuser", "password": "12345"})

        response = self.client.get("/logout", follow_redirects=True)

        self.assertIn("Вы вышли из системы.", response.data.decode("utf-8"))


if __name__ == "__main__":
    unittest.main()
