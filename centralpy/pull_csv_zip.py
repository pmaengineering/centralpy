import datetime
import logging
from pathlib import Path

from centralpy.response.csvzip import CsvZip


logger = logging.getLogger(__name__)


def pull_csv_zip(client, project: str, form_id: str, csv_dir: Path, zip_dir: Path):
    csv_zip = client.export_submissions_to_csv_zip(project, form_id)
    logger.info("CSV zip download complete for form_id %s", form_id)
    full_zip_filename = csv_zip.save_zip(zip_dir)
    logger.info("Zip saved to %s", full_zip_filename)
    files = csv_zip.save_data(csv_dir)
    for item in files:
        logger.info('Into directory %s, CSV data file saved: "%s"', csv_dir, item)


def keep_recent_zips(keep: int, form_id: str, zip_dir: Path, suffix_format: str = None):
    if keep < 1:
        return
    zips = list(zip_dir.glob(f"{form_id}*.zip"))
    result = []
    for zip_path in zips:
        stem = zip_path.stem
        time_suffix = stem[len(form_id) :]
        fmt = CsvZip.ZIPFILE_SUFFIX if suffix_format is None else suffix_format
        try:
            date_time = datetime.datetime.strptime(time_suffix, fmt)
            result.append((date_time, zip_path))
        except ValueError:
            pass
    if len(zips) != len(result):
        logger.warn(
            'In directory %s, %d zip files start with "%s", but only %d have date information in the file name.',
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
