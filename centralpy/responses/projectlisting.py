"""A module for the ProjectListing class."""


class ProjectListing:
    """A class to respresent a projects listing."""

    def __init__(self, response):
        self.response = response

    def can_access_project(self, project: str):
        """Check if the provided project ID is in the response"""
        return any(int(project) == item["id"] for item in self.response.json())

    def get_projects(self):
        """Return the list of projects."""
        return self.response.json()

    def __repr__(self):
        return f"ProjectListing({self.response!r})"
