"""A module for the SubmissionListing class."""


class SubmissionListing:
    """A class to respresent a submissions listing."""

    def __init__(self, response):
        self.response = response

    def has_instance_id(self, instance_id: str):
        """Check if the listing has the instance_id."""
        return any(instance_id == item["instanceId"] for item in self.get_submissions())

    def get_submissions(self):
        """Return the list of projects."""
        return self.response.json()

    def print_most_recent(self):
        """Print the most recent submission."""
        submissions = self.get_submissions()
        if submissions:
            most_recent = sorted(submissions, key=lambda x: x["createdAt"])[0]
            print(
                f'-> Most recent submission is from "{most_recent["createdAt"]}" '
                f'and has instance ID "{most_recent["instanceId"]}". Total '
                f"submission count: {len(submissions)}"
            )
        else:
            print("-> No submissions found.")

    def __repr__(self):
        return f"SubmisionListing({self.response!r})"
