"""Module for possible ODK Central responses."""
from centralpy.responses.csvzip import CsvZip


class Response:
    """A class representing a response from the server."""

    def __init__(self, response):
        self.response = response

    def json(self):
        """Return the response as a JSON object."""
        return self.response.json()
