from pathlib import Path

from requests.models import Response


class Attachment:
    """A class to respresent an attachment."""

    def __init__(self, response: Response):
        self.response = response

    @property
    def text(self):
        return self.response.text

    def save(self, filename: Path):
        with open(filename, mode="w", encoding="utf-8") as f:
            f.write(self.response.text)

    def get_filename_from_header(self):
        content_disposition = self.response.headers.get("Content-Disposition")
        if not content_disposition:
            return None
        quoted_filename = content_disposition.split("=")[-1]
        return quoted_filename.replace('"', "").strip()
    
    def __repr__(self):
        return f"Attachment({self.response!r})"

