"""A module for the use case of downloading a submissions zip."""
import datetime
import logging
from pathlib import Path

from centralpy.client import CentralClient
from centralpy.responses import CsvZip


logger = logging.getLogger(__name__)


# pylint: disable=too-many-arguments
def pull_csv_zip(
    client: CentralClient,
    project: str,
    form_id: str,
    csv_dir: Path,
    zip_dir: Path,
    no_attachments: bool,
    no_progress: bool,
):
    """Download the CSV zip from ODK Central."""
    csv_zip = client.get_submissions_csv_zip(
        project, form_id, no_attachments, zip_dir, no_progress
    )
    logger.info(
        "CSV zip download complete for form_id %s. Attachments included: %s",
        form_id,
        not no_attachments,
    )
    logger.info("Zip saved to %s", csv_zip.filename)
    files = csv_zip.extract_files_to(csv_dir)
    for item in files:
        logger.info('Into directory %s, CSV data file saved: "%s"', csv_dir, item)


def keep_recent_zips(keep: int, form_id: str, zip_dir: Path, suffix_format: str = None):
    """Keep only the specified number of CSV zip files in a directory."""
    if keep < 1:
        return
    zips = list(zip_dir.glob(f"{form_id}*.zip"))
    result = []
    for zip_path in zips:
        stem = zip_path.stem
        form_id_len = len(form_id)
        time_suffix = stem[form_id_len:]
        fmt = CsvZip.ZIPFILE_SUFFIX_FMT if suffix_format is None else suffix_format
        try:
            date_time = datetime.datetime.strptime(time_suffix, fmt)
            result.append((date_time, zip_path))
        except ValueError:
            pass
    if len(zips) != len(result):
        logger.warning(
            (
                'In directory %s, %d zip files start with "%s", but only %d have date '
                "information in the file name."
            ),
            zip_dir,
            len(zips),
            form_id,
            len(result),
        )
    if len(result) <= keep:
        return
    result.sort(reverse=True)
    for _, zip_path in result[keep:]:
        zip_path.unlink()
        logger.info("While deleting old zips, deleted %s", zip_path)
