"""A module for dealing with audits on ODK Central."""
from datetime import datetime, timezone
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

from requests.models import HTTPError
from tqdm import tqdm  # type: ignore
from werkzeug.utils import secure_filename

from centralpy.check_audits import AUDIT_FILENAME, check_audit_data
from centralpy.client import CentralClient
from centralpy.errors import AuditReportError


logger = logging.getLogger(__name__)


class AuditReport:  # pylint: disable=too-many-instance-attributes
    """A class to hold report details on audits on ODK Central."""

    def __init__(
        self,
        project: str,
        form_id: str,
        audit_dir: Path,
    ):
        self.project = project
        self.form_id = form_id
        self.audit_dir = audit_dir.resolve()

        self.good_audit: Dict[str, dict] = {}
        self.bad_audit: Dict[str, dict] = {}
        self.missing_audit: Dict[str, dict] = {}
        self.no_audit: Dict[str, dict] = {}
        self.last_checked: Optional[str] = None

        self.checked_at: str = get_now_isoformat()
        self.count_checked: int = 0

    def get_audit_path(self, path: Path) -> Path:
        """Give the full path to an audit file."""
        return self.audit_dir / path

    def should_check(self, instance_id: str) -> bool:
        """Decide if an instance should have its audit reviewed."""
        return instance_id not in self.good_audit and instance_id not in self.no_audit

    def pop_from_all(self, instance_id: str):
        """Remove an instance ID from all audit classifications."""
        self.good_audit.pop(instance_id, None)
        self.bad_audit.pop(instance_id, None)
        self.missing_audit.pop(instance_id, None)
        self.no_audit.pop(instance_id, None)

    def add_good_audit(self, instance_id: str):
        """Add an instance ID to the good audit list."""
        self._add_to(self.good_audit, instance_id)

    def add_bad_audit(self, instance_id: str, bad_records: list, audit_path: str):
        """Add an instance ID to good or bad audit list."""
        self._add_to(
            self.bad_audit,
            instance_id,
            bad_records=bad_records,
            audit_path=audit_path,
        )

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
        audit_path: str = None,
    ):
        self.pop_from_all(instance_id)
        audit_dict: dict = dict(checked_at=self.checked_at)
        if bad_records:
            audit_dict["bad_records"] = bad_records
        if audit_path:
            audit_dict["audit_path"] = str(audit_path)
        audit_obj[instance_id] = audit_dict
        self.count_checked += 1

    def mark_as_corrected(self, corrected_instance_ids: List[str]) -> None:
        """Move instances with corrected audits to the good audit list."""
        for instance_id in corrected_instance_ids:
            audit_dict = self.bad_audit.pop(instance_id)
            audit_dict.pop("bad_records")
            audit_dict.pop("audit_path")
            audit_dict["checked_at"] = self.checked_at
            self.good_audit[instance_id] = audit_dict
        self.count_checked += len(corrected_instance_ids)

    @classmethod
    def from_json(cls, filename: Path):
        """Load an audit report from JSON."""
        with open(filename, encoding="utf-8") as f:
            obj = json.load(f)
            audit_report = cls(
                project=obj["project"],
                form_id=obj["form_id"],
                audit_dir=Path(obj["audit_dir"]),
            )
            audit_report.good_audit = obj["good_audit"]
            audit_report.bad_audit = obj["bad_audit"]
            audit_report.missing_audit = obj["missing_audit"]
            audit_report.no_audit = obj["no_audit"]
            audit_report.last_checked = obj["last_checked"]
            return audit_report

    def to_json(self, filename: Path):
        """Save an audit report to JSON."""
        filename.parent.mkdir(parents=True, exist_ok=True)
        with open(filename, mode="w", encoding="utf-8") as f:
            json.dump(
                dict(
                    project=self.project,
                    form_id=self.form_id,
                    audit_dir=str(self.audit_dir),
                    good_audit=self.good_audit,
                    bad_audit=self.bad_audit,
                    missing_audit=self.missing_audit,
                    no_audit=self.no_audit,
                    last_checked=self.last_checked,
                ),
                f,
                indent=2,
            )

    def __len__(self):
        return (
            len(self.good_audit)
            + len(self.bad_audit)
            + len(self.missing_audit)
            + len(self.no_audit)
        )


def repair_server_audits_from_report(
    client: CentralClient,
    report_file: Path,
):
    """Repair audit files on ODK Central from an audit report."""
    audit_report = AuditReport.from_json(report_file)
    project = audit_report.project
    form_id = audit_report.form_id
    logger.info(
        'Repairing audit files for project "%s", form_id "%s", from directory "%s".',
        project,
        form_id,
        audit_report.audit_dir,
    )
    corrected_instance_ids = []
    for audit in audit_report.bad_audit.values():
        instance_id = audit["instance_id"]
        audit_path = audit_report.get_audit_path(audit["audit_path"])
        if not audit_path.exists():
            logger.warning(
                'Audit expected at "%s" for instance "%s" but audit file not found.',
                audit_path,
                instance_id,
            )
            continue
        data = audit_path.read_bytes()
        bad_records = check_audit_data(data)
        if bad_records:
            logger.warning(
                'Audit at "%s" still has bad records. Not uploading.',
                audit_path,
            )
            continue
        try:
            client.post_attachment(project, form_id, instance_id, AUDIT_FILENAME, data)
            corrected_instance_ids.append(instance_id)
        except HTTPError as e:
            logger.warning(
                'Server sent this error code: %d. Unable to upload corrected audit for instance "%s".',
                e.response.status_code,
                instance_id,
            )
    audit_report.mark_as_corrected(corrected_instance_ids)
    logger.info("Count of repaired audits: %d", len(corrected_instance_ids))
    if corrected_instance_ids:
        audit_report.to_json(report_file)
        logger.info('Saved report file to "%s"', report_file)
    return audit_report


def make_server_audit_report(  # pylint: disable=too-many-arguments
    client: CentralClient,
    project: str,
    form_id: str,
    audit_dir: Path,
    report_file: Path,
    relative_time: Optional[str],
    since_prev: bool,
) -> AuditReport:
    """Report on audit file correctness on an ODK Central server for a form."""
    audit_report = get_prev_or_new_audit_report(
        report_file, project, form_id, audit_dir
    )
    instances_to_check = get_instances_to_check(
        audit_report, client, project, form_id, relative_time, since_prev
    )
    check_all_audits_save_bad_audits(
        audit_report, instances_to_check, client, project, form_id
    )
    audit_report.last_checked = audit_report.checked_at
    audit_report.to_json(report_file)
    logger.info('Saved server audit report to "%s"', report_file)
    return audit_report


def get_prev_or_new_audit_report(
    report_file: Path, project: str, form_id: str, audit_dir: Path
) -> AuditReport:
    """
    Get the audit report from file, if it exists.

    If it does not exist, then a new one is initialized and returned.
    """
    if report_file.exists():
        audit_report = AuditReport.from_json(report_file)
        if (
            audit_report.project != project
            or audit_report.form_id != form_id
            or not audit_dir.resolve() == audit_report.audit_dir
        ):
            raise AuditReportError(
                f'AuditReport from "{report_file}" does not match '
                f"project {project}, form_id {form_id}, and audit_dir {audit_dir}",
                report_file,
                project,
                form_id,
                audit_dir,
            )
        logger.debug(
            'Previous audit results file found at "%s". Has information on %d submission(s)',
            report_file,
            len(audit_report),
        )
    else:
        audit_report = AuditReport(project, form_id, audit_dir)
        logger.debug(
            'No previous audit results file found at "%s". Creating a new one.',
            report_file,
        )
    return audit_report


def get_instances_to_check(  # pylint: disable=too-many-arguments
    audit_report: AuditReport,
    client: CentralClient,
    project: str,
    form_id: str,
    relative_time: Optional[str],
    since_prev: bool,
) -> List[str]:
    """Get the list of instance IDs to check for malformed audits."""
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
        'Total submissions for form "%s": %d. '
        "After filtering by relative time %s and absolute time %s, recent submissions: %d. "
        "After keeping those that need to be checked, number to check: %d",
        form_id,
        len(submission_listing),
        repr(relative_time),
        repr(absolute_time),
        len(recent_submissions),
        len(instances_to_check),
    )
    return instances_to_check


def check_all_audits_save_bad_audits(
    audit_report: AuditReport,
    instances_to_check: List[str],
    client: CentralClient,
    project: str,
    form_id: str,
):
    """Check all audits from a list, save bad audits to disk."""
    if not instances_to_check:
        return
    bad_audits: List[str] = []
    for instance_id in tqdm(
        instances_to_check,
        desc="Submissions",
        ascii=True,
    ):
        try:
            attachment = client.get_attachment(
                project, form_id, instance_id, AUDIT_FILENAME
            )
            csvfile = attachment.text.splitlines()
            bad_records = check_audit_data(csvfile)
            if bad_records:
                sub_path = Path(secure_filename(instance_id)) / AUDIT_FILENAME
                full_path = audit_report.audit_dir / sub_path
                full_path.parent.mkdir(parents=True, exist_ok=True)
                full_path.write_bytes(attachment.content)
                audit_report.add_bad_audit(instance_id, bad_records, str(sub_path))
                bad_audits.append(instance_id)
            else:
                audit_report.add_good_audit(instance_id)
        except HTTPError:
            attachment_listing = client.get_attachments(project, form_id, instance_id)
            if attachment_listing.has_attachment(AUDIT_FILENAME):
                audit_report.add_missing_audit(instance_id)
            else:
                audit_report.add_no_audit(instance_id)
    if bad_audits:
        logger.info(
            'Count of bad audits: %d. All saved to audit directory "%s".',
            len(bad_audits),
            audit_report.audit_dir,
        )


def get_now_isoformat():
    """Get now (date and time) in ISO format with milliseconds."""
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")
