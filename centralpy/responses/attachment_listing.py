"""A module for the AttachmentListing class."""
from typing import List

from requests.models import Response


class AttachmentListing:
    """A class to respresent an attachments listing."""

    def __init__(self, response: Response):
        self.response = response

    def has_attachment(self, filename: str) -> bool:
        """Check if the attachment listing has the filename."""
        return any(filename == item["name"] for item in self.get_attachments())

    def get_attachments(self) -> list:
        """Return the list of attachments."""
        return self.response.json()

    def get_attachment_filenames(self) -> List[str]:
        """Return a list of all attachment filenames."""
        return [item["name"] for item in self.get_attachments()]

    def print_all(self) -> None:
        """Print all attachments."""
        attachments = self.get_attachments()
        if not attachments:
            print("-> No attachments found")
        else:
            for item in attachments:
                print(f'-> name: "{item["name"]}", exists: {item["exists"]}')

    def __repr__(self):
        return f"AttachmentListing({self.response!r})"
