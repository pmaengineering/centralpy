"""A module to define the CentralClient class."""
import logging

import requests
from requests.exceptions import RequestException

from centralpy.errors import AuthenticationError
from centralpy.responses import (
    AttachmentListing,
    CsvZip,
    FormListing,
    ProjectListing,
    Response,
    SubmissionListing,
)


logger = logging.getLogger(__name__)


class CentralClient:
    """A class representing a client for ODK Central."""

    # fmt: off
    VERSION = "/version.txt"
    API_SESSIONS = "/v1/sessions"
    API_PROJECTS = "/v1/projects"
    API_PROJECT_DETAILS = "/v1/projects/{project}"
    API_FORMS = "/v1/projects/{project}/forms"
    API_FORM_DETAILS = "/v1/projects/{project}/forms/{form_id}"
    API_SUBMISSIONS = "/v1/projects/{project}/forms/{form_id}/submissions"
    API_SUBMISSIONS_EXPORT = "/v1/projects/{project}/forms/{form_id}/submissions.csv.zip"
    API_ATTACHMENTS = "/v1/projects/{project}/forms/{form_id}/submissions/{instance_id}/attachments"
    API_ATTACHMENT_DETAILS = "/v1/projects/{project}/forms/{form_id}/submissions/{instance_id}/attachments/{filename}"
    # fmt: on

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

    def _raise_exception_if_missing_auth_info(self):
        if not self.url or not self.email or not self.password:
            email = f'"{self.email or "missing"}"'
            password = f'"{self.password or "missing"}"'
            url = f'"{self.url or "missing"}"'
            raise AuthenticationError(
                "Not enough information for authentication provided: "
                f"email is {email}, password is {password}, server URL is {url}."
            )

    def create_session_token(self) -> None:
        """Create a session token by authenticating with ODK Central."""
        self._raise_exception_if_missing_auth_info()
        resp = requests.post(
            f"{self.url}{self.API_SESSIONS}", json=self._get_auth_dict()
        )
        if resp.status_code == 200:
            logger.info("Successfully authenticated and obtained session token")
        else:
            logger.warning(
                "ODK Central was unable to authenticate the provided credentials"
            )
        resp.raise_for_status()
        self.session_token = resp.json()["token"]

    def ensure_session(self) -> None:
        """Ensure the client has a session token."""
        if self.session_token is None:
            self.create_session_token()

    def get_version(self) -> Response:
        """Get the server version information."""
        if self.url is None:
            raise RequestException("Client is not configured with a URL.")
        resp = requests.get(f"{self.url}{self.VERSION}")
        return Response(resp)

    def get_projects(self) -> ProjectListing:
        """Get the projects listing."""
        self.ensure_session()
        resp = requests.get(
            f"{self.url}{self.API_PROJECTS}", headers=self._get_auth_header()
        )
        resp.raise_for_status()
        return ProjectListing(resp)

    def get_forms(self, project: str) -> FormListing:
        """Get the forms listing for the specified project."""
        self.ensure_session()
        forms_url = self.API_FORMS.format(project=project)
        resp = requests.get(f"{self.url}{forms_url}", headers=self._get_auth_header())
        resp.raise_for_status()
        return FormListing(resp)

    def get_submissions(self, project: str, form_id: str) -> SubmissionListing:
        """Get the submission listing for the specified form."""
        self.ensure_session()
        submissions_url = self.API_SUBMISSIONS.format(project=project, form_id=form_id)
        resp = requests.get(
            f"{self.url}{submissions_url}", headers=self._get_auth_header()
        )
        resp.raise_for_status()
        return SubmissionListing(resp)

    def get_attachments(
        self, project: str, form_id: str, instance_id: str
    ) -> AttachmentListing:
        """Get the attachment listing for the specified instance."""
        self.ensure_session()
        attachments_url = self.API_ATTACHMENTS.format(
            project=project, form_id=form_id, instance_id=instance_id
        )
        resp = requests.get(
            f"{self.url}{attachments_url}", headers=self._get_auth_header()
        )
        resp.raise_for_status()
        return AttachmentListing(resp)

    def get_submissions_csv_zip(
        self, project: str, form_id: str, no_attachments: bool
    ) -> CsvZip:
        """Get the submissions CSV zip."""
        self.ensure_session()
        export_url = self.API_SUBMISSIONS_EXPORT.format(
            project=project, form_id=form_id
        )
        params = {}
        if no_attachments:
            params["attachments"] = "false"
        resp = requests.get(
            f"{self.url}{export_url}", params=params, headers=self._get_auth_header()
        )
        resp.raise_for_status()
        return CsvZip(resp, form_id)

    def post_submission(self, project: str, form_id: str, data: bytes) -> Response:
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

    def post_attachment(  # pylint: disable=too-many-arguments
        self, project: str, form_id: str, instance_id: str, filename: str, data: bytes
    ):
        """Post an attachment to a submission in ODK Central."""
        self.ensure_session()
        add_attachment_url = self.API_ATTACHMENT_DETAILS.format(
            project=project, form_id=form_id, instance_id=instance_id, filename=filename
        )
        resp = requests.post(
            f"{self.url}{add_attachment_url}",
            headers={"Content-type": "*/*", **self._get_auth_header()},
            data=data,
        )
        resp.raise_for_status()
        return Response(resp)
