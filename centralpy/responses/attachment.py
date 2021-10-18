"""A module for the Attachment class."""
from pathlib import Path
from typing import Optional

from requests.models import Response


class Attachment:
    """A class to respresent an attachment."""

    def __init__(self, response: Response):
        self.response = response

    @property
    def text(self) -> str:
        """Return the response data as a string."""
        return self.response.text

    def save(self, filename: Path) -> None:
        """Save the attachment to a file."""
        with open(filename, mode="wb") as f:
            f.write(self.response.content)

    def get_filename_from_header(self) -> Optional[str]:
        """Get the server-suggested filename."""
        content_disposition = self.response.headers.get("Content-Disposition")
        if not content_disposition:
            return None
        quoted_filename = content_disposition.split("=")[-1]
        return quoted_filename.replace('"', "").strip()

    def __repr__(self):
        return f"Attachment({self.response!r})"
