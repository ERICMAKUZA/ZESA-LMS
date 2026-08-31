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

    def create_course(
        self,
        *,
        shortname: str,
        fullname: str,
        category_id: int,
        summary: str,
        visible: bool,
    ) -> dict:
        result = self._call(
            "core_course_create_courses",
            **{
                "courses[0][shortname]": shortname,
                "courses[0][fullname]": fullname,
                "courses[0][categoryid]": category_id,
                "courses[0][summary]": summary,
                "courses[0][summaryformat]": 1,
                "courses[0][visible]": int(visible),
            },
        )
        if not isinstance(result, list) or not result or not result[0].get("id"):
            raise RuntimeError("Moodle did not return the new course ID.")
        return result[0]

    def update_course(
        self,
        *,
        course_id: int,
        shortname: str,
        fullname: str,
        category_id: int,
        summary: str,
        visible: bool,
    ) -> dict | list:
        return self._call(
            "core_course_update_courses",
            **{
                "courses[0][id]": course_id,
                "courses[0][shortname]": shortname,
                "courses[0][fullname]": fullname,
                "courses[0][categoryid]": category_id,
                "courses[0][summary]": summary,
                "courses[0][summaryformat]": 1,
                "courses[0][visible]": int(visible),
            },
        )

    def delete_course(self, course_id: int) -> dict | list:
        return self._call(
            "core_course_delete_courses",
            **{"courseids[0]": course_id},
        )

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
