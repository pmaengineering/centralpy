"""A module to define the CentralClient class."""
import requests

from centralpy.errors import AuthenticationError
from centralpy.responses import Response, CsvZip


class CentralClient:
    """A class representing a client for ODK Central."""

    API_SESSIONS = "/v1/sessions"
    API_EXPORT_SUBMISSIONS = (
        "/v1/projects/{project}/forms/{form_id}/submissions.csv.zip"
    )
    API_SUBMISSIONS = "/v1/projects/{project}/forms/{form_id}/submissions"
    API_ATTACHMENTS = (
        "/v1/projects/{project}/forms/{form_id}/submissions/{instance_id}/attachments"
    )
    API_ADD_ATTACHMENT = "/v1/projects/{project}/forms/{form_id}/submissions/{instance_id}/attachments/{filename}"

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

    def create_session_token(self) -> None:
        """Create a session token by authenticating with ODK Central."""
        if not self.url or not self.email or not self.password:
            raise AuthenticationError(
                "Not enough information for authentication provided: email is "
                f'"{self.email}", password is "{self.password}", server URL is "{self.url}"'
            )
        resp = requests.post(
            f"{self.url}{self.API_SESSIONS}", json=self._get_auth_dict()
        )
        resp.raise_for_status()
        self.session_token = resp.json()["token"]

    def ensure_session(self) -> None:
        """Ensure the client has a session token."""
        if self.session_token is None:
            self.create_session_token()

    def get_submissions_csv_zip(self, project: str, form_id: str) -> CsvZip:
        """Get the submissions CSV zip."""
        self.ensure_session()
        export_url = self.API_EXPORT_SUBMISSIONS.format(
            project=project, form_id=form_id
        )
        resp = requests.get(f"{self.url}{export_url}", headers=self._get_auth_header())
        resp.raise_for_status()
        return CsvZip(resp, form_id)

    def post_submission(self, project: str, form_id: str, data):
        """Post a submission to ODK Central."""
        self.ensure_session()
        submission_url = self.API_SUBMISSIONS.format(project=project, form_id=form_id)
        resp = requests.post(
            f"{self.url}{submission_url}",
            headers={"Content-type": "text/xml", **self._get_auth_header()},
            data=data,
        )
        resp.raise_for_status()
        return Response(resp)

    def post_attachment(self, project, form_id, instance_id, filename, data):
        """Post an attachment to a submission in ODK Central."""
        self.ensure_session()
        add_attachment_url = self.API_ADD_ATTACHMENT.format(
            project=project, form_id=form_id, instance_id=instance_id, filename=filename
        )
        resp = requests.post(
            f"{self.url}{add_attachment_url}",
            headers={"Content-type": "*/*", **self._get_auth_header()},
            data=data,
        )
        resp.raise_for_status()
        return Response(resp)
