from types import SimpleNamespace
from unittest.mock import patch

from django.core.cache import cache
from django.test import SimpleTestCase, override_settings

from apps.accounts.moodle_sso import consume_moodle_sso_code, issue_moodle_sso_code


@override_settings(
    MOODLE_BASE_URL="https://moodle.example.test",
    MOODLE_SSO_SHARED_SECRET="test-shared-secret",
    MOODLE_SSO_CODE_TTL_SECONDS=120,
    CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}},
)
class MoodleSsoCodeTests(SimpleTestCase):
    def setUp(self):
        cache.clear()
        self.user = SimpleNamespace(
            email="learner@zesa.co.zw",
            zntc_email="learner@students.zntc.ac.zw",
            first_name="Test",
            last_name="Learner",
        )

    @patch("apps.accounts.moodle_sso._active_course_ids", return_value=[12, 25])
    def test_code_can_be_consumed_only_once(self, _active_course_ids):
        code = issue_moodle_sso_code(self.user)

        self.assertEqual(
            consume_moodle_sso_code(code),
            {
                "user": {
                    "email": "learner@students.zntc.ac.zw",
                    "username": "learner",
                    "firstname": "Test",
                    "lastname": "Learner",
                },
                "course_ids": [12, 25],
            },
        )
        self.assertIsNone(consume_moodle_sso_code(code))

    def test_invalid_code_is_rejected(self):
        self.assertIsNone(consume_moodle_sso_code("not-a-valid-moodle-sso-code"))
