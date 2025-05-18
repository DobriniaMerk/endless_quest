import unittest
from questsite.__init__ import create_app
import os
import tempfile
from werkzeug.security import generate_password_hash

class AuthTestCase(unittest.TestCase):
    def setUp(self):
        # Создание временной БД
        self.db_fd, self.db_path = tempfile.mkstemp()
        self.app = create_app({
            "TESTING": True,
            "DATABASE_PATH": self.db_path,
            "SECRET_KEY": "test",
        })
        self.client = self.app.test_client()

        # Инициализация БД
        with self.app.app_context():
            from questsite import auth
            from questsite.db import DB

            db = DB(self.db_path, schema_path="questsite/schema.sql")
            auth._db = db
            db.add_user("testuser", "test@example.com", "12345")


    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(self.db_path)

    def test_register(self):
        response = self.client.post("/register", data={
            "username": "newuser",
            "email": "new@example.com",
            "password": "pass123"
        }, follow_redirects=True)

        self.assertIn("newuser".encode("utf-8"), response.data)

    def test_register_duplicate(self):
        response = self.client.post("/register", data={
            "username": "testuser",
            "email": "another@example.com",
            "password": "pass456"
        }, follow_redirects=True)

        self.assertIn("Имя пользователя уже существует".encode("utf-8"), response.data)

    def test_login_success(self):
        response = self.client.post("/login", data={
            "username": "testuser",
            "password": "12345"
        }, follow_redirects=True)

        self.assertIn(b"testuser", response.data)

    def test_login_wrong_password(self):
        response = self.client.post("/login", data={
            "username": "testuser",
            "password": "wrongpassword"
        }, follow_redirects=True)

        self.assertIn("Неправильное имя пользователя или пароль".encode("utf-8"), response.data)

    def test_logout(self):
        self.client.post("/login", data={
            "username": "testuser",
            "password": "12345"
        })

        response = self.client.get("/logout", follow_redirects=True)

        self.assertIn("Вы вышли из системы.".encode("utf-8"), response.data)

    
if __name__ == '__main__':
    unittest.main()
