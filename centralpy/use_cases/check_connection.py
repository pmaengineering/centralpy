"""A module to check the connection for centralpy."""
from enum import Enum
from typing import Optional

from requests.exceptions import RequestException, HTTPError

from centralpy.client import CentralClient
from centralpy.errors import AuthenticationError


class Check(Enum):
    """An enumeration of all checks performed."""

    CONNECT = "1. Connect to the server"
    VERIFY = "2. Verify the server is an ODK Central server"
    AUTH = "3. Authenticate the provided credentials"
    PROJECT = "4. Check existence and access to the project, if provided"
    FORM_ID = (
        "5. Check existence and access to the form ID within the project, if provided"
    )

    def success_msg(self) -> str:
        """Format the message for success."""
        return f"Success:    {self.value}"

    def failure_msg(self) -> str:
        """Format the message for failure."""
        return f"Failure:    {self.value}"

    def skip_msg(self) -> str:
        """Format the message for a skip."""
        return f"Skip:       {self.value}"


def check_connect_and_verify(client: CentralClient) -> bool:
    """Check the connection and verify the server is ODK Central."""
    try:
        resp = client.get_version()
        print(Check.CONNECT.success_msg())
        if resp.ok and all(i in resp.text for i in ("versions", "client", "server")):
            print(Check.VERIFY.success_msg())
        else:
            print(Check.VERIFY.failure_msg())
            print(
                f"-> Could not verify that this server is ODK Central by checking: {resp.url}"
            )
            return False
    except RequestException:
        print(Check.CONNECT.failure_msg())
        print(
            f"-> Check the internet connection and the spelling of the server URL: {client.url}"
        )
        return False
    return True


def check_auth(client: CentralClient) -> bool:
    """Check that ODK Central can authenticate the provided credentials."""
    try:
        client.create_session_token()
        print(Check.AUTH.success_msg())
    except HTTPError as err:
        print(Check.AUTH.failure_msg())
        print(
            "-> ODK Central was unable to authenticate the provided credentials. Please verify email/password."
        )
        return False
    except AuthenticationError as err:
        print(Check.AUTH.failure_msg())
        print(err)
        return False
    return True


# pylint: disable=unsubscriptable-object
def check_project(client: CentralClient, project: Optional[str]) -> bool:
    """Check that the provided project is accessible."""
    project_listing = client.get_projects()
    projects = project_listing.get_projects()
    if project is None:
        print(Check.PROJECT.skip_msg())
        print(Check.FORM_ID.skip_msg())
        print(
            "-> No project ID was provided. These are this user's projects accessible on ODK Central:"
        )
        for item in projects:
            print(f'-> Project {item["id"]}, named "{item["name"]}"')
        return True
    if project_listing.can_access_project(project):
        print(Check.PROJECT.success_msg())
        return True
    print(Check.PROJECT.failure_msg())
    if projects:
        print(
            f"-> No access for project {project}. These are this user's projects accessible on ODK Central:"
        )
        for item in projects:
            print(f'-> Project {item["id"]}, named "{item["name"]}"')
    else:
        print(
            "-> No projects are able to be accessed. Have an administrator add this user as a Project Manager."
        )
    return False


# pylint: disable=unsubscriptable-object
def check_form_id(client: CentralClient, project: str, form_id: Optional[str]) -> bool:
    """Check that the provided form ID is a form in the project."""
    form_listing = client.get_forms(project=project)
    forms = form_listing.get_forms()
    if form_id is None:
        print(Check.FORM_ID.skip_msg())
        print("-> No form ID was provided. These forms were found on ODK Central:")
        for form in forms:
            print(f'-> Form ID "{form["xmlFormId"]}", named "{form["name"]}"')
        return True
    if form_listing.has_form_id(form_id):
        print(Check.FORM_ID.success_msg())
    else:
        print(Check.FORM_ID.failure_msg())
        if forms:
            print(
                f'-> Unable to find form ID "{form_id}" in project {project}. These forms were found:'
            )
            for form in forms:
                print(f'-> Form ID "{form["xmlFormId"]}", named "{form["name"]}"')
        else:
            print(f"-> No forms found in project {project}.")
        return False


# pylint: disable=unsubscriptable-object
def check_connection(
    client: CentralClient, project: Optional[str], form_id: Optional[str]
) -> bool:
    """Check the connection, configuration, and parameters for centralpy.

    Returns:
        True if the check was successful. False if the check was not
        successful.
    """
    connect_and_verify = check_connect_and_verify(client)
    if not connect_and_verify:
        return False
    auth = check_auth(client)
    if not auth:
        return False
    has_project = check_project(client, project)
    if project is None:
        return True
    if not has_project:
        return False
    has_form_id = check_form_id(client, project, form_id)
    if not has_form_id:
        return False
    return True
