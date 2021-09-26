"""A module for the AttachmentListing class."""


class AttachmentListing:
    """A class to respresent an attachments listing."""

    def __init__(self, response):
        self.response = response

    def has_attachment(self, attachment: str):
        """Check if the listing has the instance_id."""
        return any(attachment == item["name"] for item in self.get_attachments())

    def get_attachments(self):
        """Return the list of projects."""
        return self.response.json()

    def print_all(self):
        """Print all attachments."""
        attachments = self.get_attachments()
        if not attachments:
            print("-> No attachments found")
        else:
            for item in attachments:
                print(f'-> name: "{item["name"]}", exists: {item["exists"]}')

    def __repr__(self):
        return f"AttachmentListing({self.response!r})"
