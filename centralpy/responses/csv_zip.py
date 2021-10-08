"""A module for handling responses to the export submissions URL."""
import datetime
from pathlib import Path
from typing import List
import zipfile

from requests.models import CONTENT_CHUNK_SIZE, Response
from tqdm import tqdm


class CsvZip:
    """A class representing a response to the export submissions URL."""

    ZIPFILE_SUFFIX_FMT = "-%Y-%m-%dT%H-%M-%S"

    def __init__(self, filename: str, form_id: str, response: Response):
        self.filename = filename
        self.form_id = form_id
        self.response = response

    @classmethod
    def save_zip(
        cls,
        response: Response,
        out_dir: Path,
        form_id: str,
        no_progress_bar: bool = False,
    ) -> Path:
        """Save the zip to a directory."""
        suffix = datetime.datetime.utcnow().strftime(cls.ZIPFILE_SUFFIX_FMT)
        out_file = f"{form_id}{suffix}.zip"
        out_dir.mkdir(parents=True, exist_ok=True)
        full_filename = out_dir / out_file
        with open(full_filename, mode="wb") as f:
            with tqdm(
                unit="B",
                unit_scale=True,
                unit_divisor=1024,
                miniters=1,
                desc=str(full_filename),
                total=int(response.headers.get("content-length", 0)),
                ascii=True,
                disable=no_progress_bar,
            ) as pbar:
                for chunk in response.iter_content(chunk_size=CONTENT_CHUNK_SIZE):
                    f.write(chunk)
                    pbar.update(len(chunk))
        return cls(full_filename, form_id, response)

    def extract_files_to(self, out_dir: Path) -> List[str]:
        """Extract CSV data files to a directory."""
        saved = []
        out_dir.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(self.filename) as z:
            for zip_info in z.infolist():
                if zip_info.filename.startswith("media/"):
                    continue
                z.extract(zip_info, path=out_dir)
                saved.append(zip_info.filename)
        return saved

    def __repr__(self):
        return f'CsvZip(filename="{self.filename}", form_id="{self.form_id}")'
