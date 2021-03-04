"""A module for the FormListing class."""


class FormListing:
    """A class to respresent a forms listing."""

    def __init__(self, response):
        self.response = response

    def has_form_id(self, form_id):
        """Check if the listing has the form_id."""
        return any(form_id == item["xmlFormId"] for item in self.response.json())

    def get_forms(self):
        """Return the list of forms."""
        return self.response.json()

    def __repr__(self):
        return f"FormListing({self.response!r})"
