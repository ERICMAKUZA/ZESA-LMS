from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone as dt_timezone
from typing import Union

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class MoodleAPIError(Exception):
    def __init__(self, message: str, raw_response=None):
        super().__init__(message)
        self.raw_response = raw_response


class MoodleEnrollmentService:
    def __init__(self):
        self.base_url = settings.MOODLE_BASE_URL.rstrip("/")
        self.wstoken = settings.MOODLE_WSTOKEN
        self._endpoint = f"{self.base_url}/webservice/rest/server.php"

    def _call(self, wsfunction: str, params: dict) -> Union[dict, list]:
        payload = {
            "wstoken": self.wstoken,
            "wsfunction": wsfunction,
            "moodlewsrestformat": "json",
            **params,
        }
        try:
            response = requests.post(self._endpoint, data=payload, timeout=30)
            response.raise_for_status()
        except requests.RequestException as exc:
            raise MoodleAPIError(f"HTTP error calling {wsfunction}: {exc}") from exc

        data = response.json()
        if isinstance(data, dict) and "exception" in data:
            raise MoodleAPIError(
                f"Moodle API error [{data.get('errorcode')}]: {data.get('message')}",
                raw_response=data,
            )
        return data

    def get_or_create_user(self, user) -> int:
        if settings.DEMO_MODE:
            fake_id = 9000 + (hash(user.email) % 1000)
            logger.info("[DEMO MODE] get_or_create_user returning fake moodle_user_id=%s for %s", fake_id, user.email)
            return fake_id

        result = self._call(
            "core_user_get_users",
            {
                "criteria[0][key]": "email",
                "criteria[0][value]": user.email,
            },
        )
        users = result.get("users", [])
        if users:
            return users[0]["id"]

        # User not in Moodle — create them.
        # Password satisfies Moodle default policy: upper, lower, digit, special char.
        temp_password = uuid.uuid4().hex[:12] + "A1!"
        create_result = self._call(
            "core_user_create_users",
            {
                "users[0][username]": user.email.lower(),
                "users[0][password]": temp_password,
                "users[0][firstname]": user.first_name or "User",
                "users[0][lastname]": user.last_name or str(user.id),
                "users[0][email]": user.email,
                "users[0][auth]": "manual",
            },
        )
        return create_result[0]["id"]

    def enroll_user(self, moodle_user_id: int, moodle_course_id: int) -> bool:
        if settings.DEMO_MODE:
            logger.info(
                "[DEMO MODE] enroll_user skipping real Moodle call (user=%s, course=%s)",
                moodle_user_id, moodle_course_id,
            )
            return True

        self._call(
            "enrol_manual_enrol_users",
            {
                "enrolments[0][roleid]": 5,  # student role
                "enrolments[0][userid]": moodle_user_id,
                "enrolments[0][courseid]": moodle_course_id,
            },
        )
        return True

    def unenroll_user(self, moodle_user_id: int, moodle_course_id: int) -> bool:
        self._call(
            "enrol_manual_unenrol_users",
            {
                "enrolments[0][userid]": moodle_user_id,
                "enrolments[0][courseid]": moodle_course_id,
            },
        )
        return True

    def get_completion_status(self, moodle_user_id: int, moodle_course_id: int) -> dict:
        return self._call(
            "core_completion_get_course_completion_status",
            {
                "courseid": moodle_course_id,
                "userid": moodle_user_id,
            },
        )

    def get_user_last_access(self, moodle_user_id: int, moodle_course_id: int) -> Union[datetime, None]:
        enrolled_users = self._call(
            "core_enrol_get_enrolled_users",
            {"courseid": moodle_course_id},
        )
        for u in enrolled_users:
            if u.get("id") == moodle_user_id:
                ts = u.get("lastaccess")
                if ts:
                    return datetime.fromtimestamp(ts, tz=dt_timezone.utc)
                return None
        return None
