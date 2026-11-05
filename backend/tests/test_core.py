import os
import unittest

os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")
os.environ.setdefault("JWT_SECRET", "test-secret-with-at-least-32-characters")

from app.seed import QUESTIONS
from app.challenge_validation import validate_auth_patch, validate_buffer_patch, validate_sql_patch
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

    def test_sql_editor_accepts_parameterized_fictional_patch(self):
        result = validate_sql_patch(
            'consulta = "SELECT * FROM usuarios WHERE nombre = ?" '
            'parametros = (nombre,) db.execute(consulta, parametros)'
        )
        self.assertTrue(result.correct)

    def test_sql_editor_rejects_concatenation(self):
        result = validate_sql_patch('consulta = "SELECT * FROM usuarios WHERE nombre = " + nombre')
        self.assertFalse(result.correct)
        self.assertTrue(result.missing)

    def test_buffer_editor_requires_length_limit(self):
        result = validate_buffer_patch("if len(entrada) > 8: return error")
        self.assertTrue(result.correct)

    def test_auth_editor_requires_multiple_defenses(self):
        result = validate_auth_patch(
            "password_policy longitud; bloqueo tras intentos; MFA; hash con sal"
        )
        self.assertTrue(result.correct)


if __name__ == "__main__":
    unittest.main()
