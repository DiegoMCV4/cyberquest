import os
import unittest

os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")
os.environ.setdefault("JWT_SECRET", "test-secret-with-at-least-32-characters")

from app.seed import QUESTIONS
from app.questions_extra import EXPANDED, EXTRA
from app.schemas import AnswerIn, Credentials


class CoreValidationTests(unittest.TestCase):
    def test_credentials_reject_invalid_username(self):
        with self.assertRaises(ValueError):
            Credentials(username="x", password="valid-password")

    def test_answer_index_is_bounded(self):
        with self.assertRaises(ValueError):
            AnswerIn(option_index=6)

    def test_question_bank_has_no_exact_duplicate_text(self):
        texts = [question[2].strip().casefold() for question in QUESTIONS + EXTRA + EXPANDED]
        self.assertEqual(len(texts), len(set(texts)))

    def test_question_bank_reaches_two_hundred_questions(self):
        self.assertGreaterEqual(11 + len(EXTRA) + len(EXPANDED), 200)


if __name__ == "__main__":
    unittest.main()
