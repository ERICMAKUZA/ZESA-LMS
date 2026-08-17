from __future__ import annotations

import logging

import httpx
from django.conf import settings

logger = logging.getLogger(__name__)


class MoodleClient:
    def __init__(self):
        self.base_url = getattr(settings, "MOODLE_API_BASE_URL", settings.MOODLE_BASE_URL).rstrip("/")
        self.wstoken = settings.MOODLE_WSTOKEN
        self._endpoint = f"{self.base_url}/webservice/rest/server.php"
        host_header = getattr(settings, "MOODLE_API_HOST_HEADER", "")
        self._headers = {"Host": host_header} if host_header else None

    def _call(self, wsfunction: str, **params) -> dict | list:
        payload = {
            "wstoken": self.wstoken,
            "wsfunction": wsfunction,
            "moodlewsrestformat": "json",
            **params,
        }
        with httpx.Client(timeout=30) as client:
            response = client.post(self._endpoint, data=payload, headers=self._headers)
        response.raise_for_status()
        data = response.json()
        if isinstance(data, dict) and "exception" in data:
            raise RuntimeError(f"Moodle API error [{data.get('errorcode')}]: {data.get('message')}")
        return data

    def get_courses(self) -> list[dict]:
        return self._call("core_course_get_courses")

    def enrol_user(self, user_id: int, course_id: int, role_id: int = 5) -> dict:
        return self._call(
            "enrol_manual_enrol_users",
            **{
                "enrolments[0][roleid]": role_id,
                "enrolments[0][userid]": user_id,
                "enrolments[0][courseid]": course_id,
            },
        )

    def get_user_course_completion(self, user_id: int, course_id: int) -> dict:
        return self._call(
            "core_completion_get_course_completion_status",
            courseid=course_id,
            userid=user_id,
        )
