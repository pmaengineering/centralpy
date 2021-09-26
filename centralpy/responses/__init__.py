"""Module for possible ODK Central responses."""
from centralpy.responses.attachment_listing import AttachmentListing
from centralpy.responses.csv_zip import CsvZip
from centralpy.responses.form_listing import FormListing
from centralpy.responses.project_listing import ProjectListing
from centralpy.responses.submission_listing import SubmissionListing


class Response:
    """A class representing a response from the server."""

    def __init__(self, response):
        self.response = response

    @property
    def text(self):
        """Return the response as text."""
        return self.response.text

    @property
    def url(self):
        """Return the response URL."""
        return self.response.url

    @property
    def ok(self):  # pylint: disable=invalid-name
        """Return if the response status code is 200."""
        return self.response.ok

    def json(self):
        """Return the response as a JSON object."""
        return self.response.json()
