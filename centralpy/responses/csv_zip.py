"""A module for handling responses to the export submissions URL."""
import datetime
from pathlib import Path
from typing import List
import zipfile

from requests.models import CONTENT_CHUNK_SIZE, Response


class CsvZip:
    """A class representing a response to the export submissions URL."""

    ZIPFILE_SUFFIX = "-%Y-%m-%dT%H-%M-%S"

    def __init__(self, response: Response, form_id: str):
        self.response = response
        self.form_id = form_id

    def save_zip(self, out_dir: Path, suffix_format: str = ZIPFILE_SUFFIX) -> Path:
        """Save the zip to a directory."""
        suffix = ""
        if suffix_format is not None:
            now = datetime.datetime.utcnow()
            suffix = now.strftime(suffix_format)
        out_file = f"{self.form_id}{suffix}.zip"
        out_dir.mkdir(parents=True, exist_ok=True)
        full_filename = out_dir / out_file
        with open(full_filename, mode="wb") as f:
            for chunk in self.response.iter_content(chunk_size=CONTENT_CHUNK_SIZE):
                f.write(chunk)
        return full_filename

    def save_data(self, in_zip_file: Path, out_dir: Path) -> List[str]:
        """Extract CSV data files to a directory."""
        saved = []
        out_dir.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(in_zip_file) as z:
            for zip_info in z.infolist():
                if zip_info.filename.startswith("media/"):
                    continue
                z.extract(zip_info, path=out_dir)
                saved.append(zip_info.filename)
        return saved

    def __repr__(self):
        return f'<CsvZip form_id="{self.form_id}">'
