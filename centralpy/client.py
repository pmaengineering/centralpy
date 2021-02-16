import io

import requests

from centralpy.error import AuthenticationException
from centralpy.response import CsvZip


class CentralClient:

    API_SESSIONS = "/v1/sessions"
    API_EXPORT_SUBMISSIONS = (
        "/v1/projects/{project_id}/forms/{form_id}/submissions.csv.zip"
    )

    def __init__(self, url: str, email: str, password: str):
        self.url = url
        self.email = email
        self.password = password
        self.session_token = None

    def _get_auth_dict(self):
        return {"email": self.email, "password": self.password}

    def _get_auth_header(self):
        self.ensure_session()
        return {"Authorization": f"Bearer {self.session_token}"}

    def create_session_token(self):
        if not self.url or not self.email or not self.password:
            raise AuthenticationException(
                "Not enough information for authentication provided: "
                f'email is "{self.email}", password is "{self.password}", server URL is "{self.url}"'
            )
        resp = requests.post(
            f"{self.url}{self.API_SESSIONS}", json=self._get_auth_dict()
        )
        resp.raise_for_status()
        self.session_token = resp.json()["token"]

    def ensure_session(self):
        if self.session_token is None:
            self.create_session_token()

    def export_submissions_to_csv_zip(self, project_id: str, form_id: str):
        self.ensure_session()
        export_url = self.API_EXPORT_SUBMISSIONS.format(
            project_id=project_id, form_id=form_id
        )
        resp = requests.get(f"{self.url}{export_url}", headers=self._get_auth_header())
        resp.raise_for_status()
        return CsvZip(resp, form_id)
