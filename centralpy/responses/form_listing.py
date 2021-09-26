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

    def print_all(self):
        """Print all forms."""
        forms = self.get_forms()
        max_width = max(len(form["xmlFormId"]) for form in forms) + 2
        for form in self.get_forms():
            form_id = f'"{form["xmlFormId"]}"'
            print(f'-> Form ID {form_id:>{max_width}}, named "{form["name"]}"')

    def __repr__(self):
        return f"FormListing({self.response!r})"
