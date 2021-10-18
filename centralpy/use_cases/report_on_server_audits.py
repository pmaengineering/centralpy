"""Inspect and report on audits that are saved in ODK Central."""
from datetime import datetime, timezone
import json
import logging
from pathlib import Path
from typing import Optional

from requests.exceptions import HTTPError
from tqdm import tqdm  # type: ignore

from centralpy.client import CentralClient
from centralpy.check_audits import AUDIT_FILENAME, check_audit_data
from centralpy.errors import AuditReportError


logger = logging.getLogger(__name__)


def report_on_server_audits(  # pylint: disable=too-many-arguments
    client: CentralClient,
    project: str,
    form_id: str,
    results_file: Path,
    relative_time: Optional[str],
    since_prev: bool,
) -> "AuditReport":
    """Report on audit file correctness on an ODK Central server."""
    audit_report = get_prev_or_new_audit_report(results_file, project, form_id)
    absolute_time = None
    if not relative_time or since_prev:
        absolute_time = audit_report.last_checked
    submission_listing = client.get_submissions(project, form_id)
    recent_submissions = submission_listing.get_most_recent(
        relative_time, absolute_time
    )
    recent_instances = [s["instanceId"] for s in recent_submissions]
    instances_to_check = list(filter(audit_report.should_check, recent_instances))
    logger.info(
        "Total submissions for form: %d. "
        "After filtering by relative time %s and absolute time %s, recent submissions: %d. "
        "Remaining to check: %d",
        len(submission_listing),
        repr(relative_time),
        repr(absolute_time),
        len(recent_submissions),
        len(instances_to_check),
    )
    for instance_id in tqdm(
        instances_to_check,
        desc="Submissions",
        ascii=True,
    ):
        check_submission_audit(audit_report, client, project, form_id, instance_id)
    audit_report.to_json(results_file)
    logger.info('Saved server audits report to "%s"', results_file)
    return audit_report


def get_prev_or_new_audit_report(
    results_file: Path, project: str, form_id: str
) -> "AuditReport":
    """
    Get the audit report from file, if it exists.

    If it does not exist, then a new one is initialized and returned.
    """
    if results_file.exists():
        audit_report = AuditReport.from_json(results_file)
        if audit_report.project != project or audit_report.form_id != form_id:
            raise AuditReportError(
                f'AuditReport from "{results_file}" does not match '
                f"project {project} and form_id {form_id}",
                results_file,
                project,
                form_id,
            )
        logger.debug(
            'Previous audit results file found at "%s". Has information on %d submission(s)',
            results_file,
            len(audit_report),
        )
    else:
        audit_report = AuditReport(project, form_id)
        logger.debug('No audit results file found at "%s". Creating...', results_file)
    return audit_report


def check_submission_audit(
    audit_results: "AuditReport",
    client: CentralClient,
    project: str,
    form_id: str,
    instance_id: str,
):
    """Check a single submission's audit and save result in report."""
    try:
        attachment = client.get_attachment(
            project, form_id, instance_id, AUDIT_FILENAME
        )
        csvfile = attachment.text.splitlines()
        bad_records = check_audit_data(csvfile)
        audit_results.add_good_or_bad_audit(instance_id, bad_records)
    except HTTPError:
        attachment_listing = client.get_attachments(project, form_id, instance_id)
        if attachment_listing.has_attachment(AUDIT_FILENAME):
            audit_results.add_missing_audit(instance_id)
        else:
            audit_results.add_no_audit(instance_id)


class AuditReport:  # pylint: disable=too-many-instance-attributes
    """A class to hold report details on audits on ODK Central."""

    def __init__(  # pylint: disable=too-many-arguments
        self,
        project: str,
        form_id: str,
        good_audit: dict = None,
        bad_audit: dict = None,
        missing_audit: dict = None,
        no_audit: dict = None,
        last_checked: str = None,
    ):
        self.project = project
        self.form_id = form_id
        self.good_audit = good_audit or {}
        self.bad_audit = bad_audit or {}
        self.missing_audit = missing_audit or {}
        self.no_audit = no_audit or {}
        self.last_checked = last_checked
        self.checked_at = datetime.now(timezone.utc).isoformat(timespec="milliseconds")
        self.count_checked = 0

    def should_check(self, instance_id: str) -> bool:
        """Decide if an instance have its audit reviewed."""
        return instance_id not in self.good_audit

    def pop_from_all(self, instance_id: str):
        """Remove an instance ID from all audit classifications."""
        self.good_audit.pop(instance_id, None)
        self.bad_audit.pop(instance_id, None)
        self.missing_audit.pop(instance_id, None)
        self.no_audit.pop(instance_id, None)

    def add_good_or_bad_audit(self, instance_id: str, bad_records: list):
        """Add an instance ID to good or bad audit list."""
        if bad_records:
            self._add_to(self.bad_audit, instance_id, bad_records)
        else:
            self._add_to(self.good_audit, instance_id)

    def add_missing_audit(self, instance_id: str):
        """Add an instance ID to the missing audit list."""
        self._add_to(self.missing_audit, instance_id)

    def add_no_audit(self, instance_id: str):
        """Add an instance ID to the no audit list."""
        self._add_to(self.no_audit, instance_id)

    def _add_to(
        self,
        audit_obj: dict,
        instance_id: str,
        bad_records: list = None,
    ):
        self.pop_from_all(instance_id)
        audit_dict: dict = dict(checked_at=self.checked_at)
        if bad_records:
            audit_dict["bad_records"] = bad_records
        audit_obj[instance_id] = audit_dict
        self.count_checked += 1

    @classmethod
    def from_json(cls, filename: Path):
        """Load an audit report from JSON."""
        with open(filename, encoding="utf-8") as f:
            obj = json.load(f)
            return cls(
                project=obj["project"],
                form_id=obj["form_id"],
                good_audit=obj["good_audit"],
                bad_audit=obj["bad_audit"],
                missing_audit=obj["missing_audit"],
                no_audit=obj["no_audit"],
                last_checked=obj["last_checked"],
            )

    def to_json(self, filename: Path):
        """Save an audit report to JSON."""
        with open(filename, mode="w", encoding="utf-8") as f:
            json.dump(
                dict(
                    project=self.project,
                    form_id=self.form_id,
                    good_audit=self.good_audit,
                    bad_audit=self.bad_audit,
                    missing_audit=self.missing_audit,
                    no_audit=self.no_audit,
                    last_checked=self.checked_at,
                ),
                f,
            )

    def __len__(self):
        return (
            len(self.good_audit)
            + len(self.bad_audit)
            + len(self.missing_audit)
            + len(self.no_audit)
        )
