import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class MoodleClient:
    def __init__(self):
        self.base_url = getattr(settings, 'MOODLE_API_BASE_URL', settings.MOODLE_BASE_URL).rstrip('/')
        self.token = settings.MOODLE_WSTOKEN
        self.api_url = f"{self.base_url}/webservice/rest/server.php"
        self.demo_mode = getattr(settings, 'DEMO_MODE', False)
        host_header = getattr(settings, 'MOODLE_API_HOST_HEADER', '')
        self.headers = {'Host': host_header} if host_header else None

    def _call(self, function, **params):
        if self.demo_mode or not self.token:
            logger.info("[DEMO] MoodleClient skipping %s", function)
            return []
        data = {
            'wstoken': self.token,
            'wsfunction': function,
            'moodlewsrestformat': 'json',
            **params,
        }
        response = requests.post(self.api_url, data=data, headers=self.headers, timeout=30)
        response.raise_for_status()
        result = response.json()
        if isinstance(result, dict) and result.get('exception'):
            raise Exception(f"Moodle API error: {result.get('message', result)}")
        return result

    def create_user(self, username, email, firstname, lastname, password):
        return self._call(
            'core_user_create_users',
            **{
                'users[0][username]': username,
                'users[0][email]': email,
                'users[0][firstname]': firstname,
                'users[0][lastname]': lastname,
                'users[0][password]': password,
                'users[0][auth]': 'manual',
            }
        )

    def enrol_user(self, moodle_user_id, moodle_course_id, role_id=5):
        return self._call(
            'enrol_manual_enrol_users',
            **{
                'enrolments[0][roleid]': role_id,
                'enrolments[0][userid]': moodle_user_id,
                'enrolments[0][courseid]': moodle_course_id,
            }
        )

    def add_to_cohort(self, moodle_user_id, cohort_id):
        return self._call(
            'core_cohort_add_cohort_members',
            **{
                'members[0][cohorttype][type]': 'id',
                'members[0][cohorttype][value]': cohort_id,
                'members[0][usertype][type]': 'id',
                'members[0][usertype][value]': moodle_user_id,
            }
        )

    def update_user_profile(self, moodle_user_id, custom_fields):
        params = {'users[0][id]': moodle_user_id}
        for i, (shortname, value) in enumerate(custom_fields.items()):
            params[f'users[0][customfields][{i}][type]'] = shortname
            params[f'users[0][customfields][{i}][value]'] = value
        return self._call('core_user_update_users', **params)
