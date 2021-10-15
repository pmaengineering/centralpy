"""A module for the SubmissionListing class."""
from datetime import datetime, timedelta, timezone
from itertools import takewhile
import re
from typing import Optional

from requests.models import Response


class SubmissionListing:
    """A class to respresent a submissions listing."""

    def __init__(self, response: Response):
        self.response = response

    def get_submissions(self, sort_desc=False) -> list:
        """Return the list of projects."""
        submissions = self.response.json()
        if sort_desc:
            submissions.sort(key=lambda x: x["createdAt"], reverse=True)
        return submissions

    def has_instance_id(self, instance_id: str) -> bool:
        """Check if the listing has the instance_id."""
        return any(instance_id == item["instanceId"] for item in self.get_submissions())

    def get_most_recent(
        self, relative_time: str = None, absolute_time: str = None
    ) -> list:
        relative_cutoff = relative_time_string_to_cutoff(relative_time)
        absolute_cutoff = absolute_time_string_to_cutoff(absolute_time)
        if not relative_cutoff and not absolute_cutoff:
            return self.get_submissions(sort_desc=True)
        cutoff = max(filter(None, [relative_cutoff, absolute_cutoff]))
        submissions = self.get_submissions(sort_desc=True)
        more_recent_than = takewhile(
            lambda x: odk_central_date_to_datetime(x["createdAt"]) > cutoff, submissions
        )
        return list(more_recent_than)

    def print_most_recent(self) -> None:
        """Print the most recent submission."""
        submissions = self.get_submissions(sort_desc=True)
        if submissions:
            most_recent = submissions[0]
            print(
                f'-> Most recent submission is from "{most_recent["createdAt"]}" '
                f'and has instance ID "{most_recent["instanceId"]}". Total '
                f"submission count: {len(submissions)}"
            )
        else:
            print("-> No submissions found.")

    def __len__(self):
        return len(self.get_submissions())

    def __repr__(self):
        return f"SubmissionListing({self.response!r})"


def absolute_time_string_to_cutoff(absolute_time: Optional[str]) -> Optional[datetime]:
    if not absolute_time:
        return None
    return datetime.fromisoformat(absolute_time)


def relative_time_string_to_cutoff(relative_time: Optional[str]) -> Optional[datetime]:
    if not relative_time:
        return None
    delta = time_string_to_time_delta(relative_time)
    if delta == timedelta():
        return None
    now = datetime.now(timezone.utc)
    cutoff = now - delta
    return cutoff


def time_string_to_time_delta(time_string: str) -> timedelta:
    hours = 0
    hours_found = re.match(r"(\d+)h", time_string)
    if hours_found:
        hours = int(hours_found.group(1))
    days = 0
    days_found = re.match(r"(\d+)d", time_string)
    if days_found:
        days = int(days_found.group(1))
    return timedelta(days=days, hours=hours)


def odk_central_date_to_datetime(date_string: str) -> datetime:
    date_time, _ = date_string.split("Z")  # _ == "" always
    return datetime.fromisoformat(f"{date_time}+00:00")
