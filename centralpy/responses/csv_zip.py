"""A module for handling responses to the export submissions URL."""
import datetime
import io
from pathlib import Path
import zipfile


class CsvZip:
    """A class representing a response to the export submissions URL."""

    ZIPFILE_SUFFIX = "-%Y-%m-%dT%H-%M-%S"

    def __init__(self, response, form_id):
        self.response = response
        self.form_id = form_id

    @property
    def zip(self):
        """Convert the response bytes to a ZipFile object."""
        return zipfile.ZipFile(io.BytesIO(self.response.content))

    def save_zip(self, out_dir: Path, suffix_format: str = ZIPFILE_SUFFIX):
        """Save the zip to a directory."""
        suffix = ""
        if suffix_format is not None:
            now = datetime.datetime.utcnow()
            suffix = now.strftime(suffix_format)
        out_file = f"{self.form_id}{suffix}.zip"
        out_dir.mkdir(parents=True, exist_ok=True)
        full_filename = out_dir / out_file
        with open(full_filename, mode="wb") as f:
            f.write(self.response.content)
        return full_filename

    def save_data(self, out_dir: Path):
        """Extract CSV data files to a directory."""
        saved = []
        this_zip = self.zip
        out_dir.mkdir(parents=True, exist_ok=True)
        for zip_info in this_zip.infolist():
            if zip_info.filename.startswith("media/"):
                continue
            this_zip.extract(zip_info, path=out_dir)
            saved.append(zip_info.filename)
        this_zip.close()
        return saved

    def __repr__(self):
        return f'<CsvZip form_id="{self.form_id}">'
