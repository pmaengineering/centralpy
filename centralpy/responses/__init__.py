"""Module for possible ODK Central responses."""
from centralpy.responses.csvzip import CsvZip
from centralpy.responses.formlisting import FormListing
from centralpy.responses.projectlisting import ProjectListing


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

    # pylint: disable=invalid-name
    @property
    def ok(self):
        """Return if the response status code is 200."""
        return self.response.ok

    def json(self):
        """Return the response as a JSON object."""
        return self.response.json()
