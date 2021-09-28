"""A module to check audit files for correctness."""
import csv
import logging
from pathlib import Path
from typing import Optional

import click


from centralpy.decorators import add_logging_options
from centralpy.loggers import setup_logging


AUDIT_FILENAME = "audit.csv"


logger = logging.getLogger("centralpy.check_audits")


def check_audit(filename: Path, record_range: Optional[range] = None):
    """Check the given audit file for correctness."""
    bad_records = []
    expected_length = -1
    with open(filename, newline="", encoding="utf-8") as csvfile:
        csvreader = csv.reader(csvfile)
        for i, row in enumerate(csvreader):
            if i == 0:
                expected_length = len(row)
                continue
            should_check = i in record_range if record_range else record_range is None
            if should_check and len(row) != expected_length:
                bad_records.append((i, row))
    return bad_records


def check_audits(dirname: Path, record_range: Optional[range] = None):
    """Check all audit files in the given directory for correctness."""
    all_bad_records = {}
    all_audits = list(dirname.glob(f"**/{AUDIT_FILENAME}"))
    logger.info(
        'Checking %d audit files under directory "%s"', len(all_audits), dirname
    )
    for audit in all_audits:
        bad_records = check_audit(audit, record_range)
        if bad_records:
            all_bad_records[audit] = bad_records
    return all_bad_records


def parse_record_option_to_range(record_input: Optional[str]) -> Optional[range]:
    """Parse a string representation of a range."""
    if not record_input:
        return None
    try:
        if "-" in record_input:
            split = record_input.split("-")
            first = int(split[0])
            last = int(split[1])
            if first > last:
                raise ValueError
        else:
            first = int(record_input)
            last = first
        logger.debug("Record range to search is %d-%d", first, last)
        return range(first, last + 1)
    except (ValueError, TypeError):
        logger.warning(
            'Unable to understand record range "%s". Searching all records.',
            record_input,
        )
        return None


@click.command()
@click.argument(
    "source-dir",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
)
@click.option(
    "--record",
    "-r",
    help="Which records to look at. Give a range or a single number. Default is all records.",
)
@add_logging_options
def main(
    source_dir: Path,
    record: str,
    log_file: str,
    verbose: bool,
):
    """
    Find audit files with incorrect number of fields in an entry.

    ODK Central expects audit files to have six fields per entry. An
    entry is usually a line. However, using quoting, a CSV field can
    span multiple lines.
    """
    setup_logging(log_file, verbose)
    logger.info(
        'Initiated search for malformed audit files at directory "%s" with range "%s"',
        source_dir,
        record,
    )
    record_range = parse_record_option_to_range(record)
    all_bad_records = check_audits(source_dir, record_range)
    for filename, bad_records in all_bad_records.items():
        print(f'Found bad CSV record(s) in "{filename}"')
        for i, bad_record in bad_records:
            print(f"-> Record {i:>4}: {bad_record}")
    if not all_bad_records:
        range_msg = ""
        if record_range:
            range_msg = f" in range {record_range.start}-{record_range.stop-1}"
        print(f'No malformed audit files were discovered at "{source_dir}"{range_msg}')
    logger.info(
        'Completed search for malformed audit files at directory "%s" with range "%s"',
        source_dir,
        record,
    )


if __name__ == "__main__":
    main()  # pylint: disable=no-value-for-parameter
