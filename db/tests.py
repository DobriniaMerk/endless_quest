import os
import tempfile
import unittest

from db import DB, clear_db

class TestDB(unittest.TestCase):
    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp(suffix=".sqlite")

        clear_db()
        self.db = DB(self.db_path, "db/schema.sql")

    def tearDown(self):
        os.close(self.db_fd)
        os.remove(self.db_path)
        clear_db()

    def assertNone(self, value):
        self.assertIsNone(value)

    def test_set_and_get_variable(self):
        self.assertNone(self.db.get_variable("foo", 1))
        self.db.set_variable("foo", 1, "bar", visible=True)
        self.assertEqual(self.db.get_variable("foo", 1), "bar")

    def test_update_variable(self):
        self.db.set_variable("x", 42, "first")
        self.assertEqual(self.db.get_variable("x", 42), "first")
        self.db.set_variable("x", 42, "second")
        self.assertEqual(self.db.get_variable("x", 42), "second")

    def test_get_user_profile_empty(self):
        self.assertEqual(self.db.get_user_profile(999), [])

    def test_get_user_profile(self):
        self.db.set_variable("a", 1, "A")
        self.db.set_variable("b", 1, "B")
        prof = {row["name"]: row["value"] for row in self.db.get_user_profile(1)}
        self.assertDictEqual(prof, {"a": "A", "b": "B"})

    def test_edit_and_get_paragraph(self):
        pid = 7
        eid1 = self.db.edit_paragraph(pid, "Story1", "Title1", protected=False, lang="ru")
        self.assertIsInstance(eid1, int)
        story, title = self.db.get_paragraph(pid, lang="ru", back_history=0)
        self.assertEqual((story, title), ("Story1", "Title1"))

        eid2 = self.db.edit_paragraph(pid, "Story2", "Title2", protected=True, lang="ru")
        self.assertNotEqual(eid1, eid2)
        self.assertEqual(self.db.get_paragraph(pid, "ru", 0), ("Story2", "Title2"))
        self.assertEqual(self.db.get_paragraph(pid, "ru", 1), ("Story1", "Title1"))

    def test_revert_paragraph_no_history(self):
        self.db.revert_paragraph(123, "en", 5)

    def test_revert_paragraph(self):
        pid = 3
        self.db.edit_paragraph(pid, "E1", "T1", lang="en")
        self.db.edit_paragraph(pid, "E2", "T2", lang="en")
        self.db.revert_paragraph(pid, "en", 1)
        story, title = self.db.get_paragraph(pid, "en", 0)
        self.assertEqual((story, title), ("E1", "T1"))


    def test_add_and_find_user(self):
        uid = self.db.add_user("u1", "u1@example.com", "pass123", is_moderator=True)
        self.assertIsInstance(uid, int)

        found = self.db.find_user("u1", "pass123")
        self.assertEqual(found, (uid, True))

        self.assertIsNone(self.db.find_user("u1", "wrong"))
        self.assertIsNone(self.db.find_user("nope", "pass123"))

    def test_is_moderator_and_userid_by_name(self):
        uid = self.db.add_user("mod", "m@e.com", "pw", is_moderator=False)
        self.assertFalse(self.db.is_moderator("mod"))
        self.assertTrue(self.db.is_moderator("mod") in (False, False))
        self.assertIsNone(self.db.is_moderator("unknown"))

        self.assertEqual(self.db.userid_by_name("mod"), uid)
        self.assertIsNone(self.db.userid_by_name("nobody"))

if __name__ == "__main__":
    unittest.main()
