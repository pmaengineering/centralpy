from datetime import datetime, timezone
import json
import logging
from pathlib import Path
from sys import audit
from typing import Optional

from requests.exceptions import HTTPError
from tqdm import tqdm

from centralpy.client import CentralClient
from centralpy.check_audits import check_audit_data


AUDIT_FILENAME = "audit.csv"


logger = logging.getLogger(__name__)


def report_on_server_audits(
    client: CentralClient,
    project: str,
    form_id: str,
    results_file: Path,
    relative_time: Optional[str],
    since_prev_results: bool,
) -> "AuditReport":
    if results_file.exists():
        audit_results = AuditReport.from_json(results_file)
        logger.debug(
            'Previous audit results file found at "%s". Has information on %d submission(s)',
            results_file,
            len(audit_results),
        )
    else:
        audit_results = AuditReport(project, form_id)
        logger.debug('No audit results file found at "%s". Creating...', results_file)
    submission_listing = client.get_submissions(project, form_id)
    absolute_time = None
    if not relative_time or since_prev_results:
        absolute_time = audit_results.last_checked
    recent_submissions = submission_listing.get_most_recent(
        relative_time, absolute_time
    )
    recent_instances = [s["instanceId"] for s in recent_submissions]
    instances_to_check = list(filter(audit_results.should_check, recent_instances))
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
        try:
            attachment = client.get_attachment(
                project, form_id, instance_id, AUDIT_FILENAME
            )
            csvfile = attachment.text.splitlines()
            bad_lines = check_audit_data(csvfile)
            audit_results.add_good_or_bad_audit(instance_id, bad_lines)
        except HTTPError:
            attachment_listing = client.get_attachments(project, form_id, instance_id)
            if attachment_listing.has_attachment(AUDIT_FILENAME):
                audit_results.add_missing_audit(instance_id)
            else:
                audit_results.add_no_audit(instance_id)
    audit_results.to_json(results_file)
    logger.info('Saved server audits report to "%s"', results_file)
    return audit_results


class AuditReport:
    def __init__(
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
        self.good_audit = good_audit or dict()
        self.bad_audit = bad_audit or dict()
        self.missing_audit = missing_audit or dict()
        self.no_audit = no_audit or dict()
        self.last_checked = last_checked
        self.checked_at = datetime.now(timezone.utc).isoformat(timespec="milliseconds")
        self.count_checked = 0

    def should_check(self, instance_id: str) -> bool:
        return instance_id not in self.good_audit

    def pop_from_all(self, instance_id: str):
        self.good_audit.pop(instance_id, None)
        self.bad_audit.pop(instance_id, None)
        self.missing_audit.pop(instance_id, None)
        self.no_audit.pop(instance_id, None)

    def add_good_or_bad_audit(self, instance_id: str, bad_lines: list):
        if bad_lines:
            self._add_to(self.bad_audit, instance_id, bad_lines)
        else:
            self._add_to(self.good_audit, instance_id)

    def add_missing_audit(self, instance_id: str):
        self._add_to(self.missing_audit, instance_id)

    def add_no_audit(self, instance_id: str):
        self._add_to(self.no_audit, instance_id)

    def _add_to(
        self,
        audit_obj: dict,
        instance_id: str,
        bad_lines: list = None,
    ):
        self.pop_from_all(instance_id)
        d = dict(checked_at=self.checked_at)
        if bad_lines:
            d["bad_lines"] = bad_lines
        audit_obj[instance_id] = d
        self.count_checked += 1

    @classmethod
    def from_json(cls, filename: Path):
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
