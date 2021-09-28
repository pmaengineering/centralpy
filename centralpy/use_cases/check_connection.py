"""A module to check the connection for centralpy."""
from enum import Enum
import logging
from typing import Optional

from requests.exceptions import RequestException, HTTPError

from centralpy.client import CentralClient
from centralpy.errors import AuthenticationError


logger = logging.getLogger(__name__)


class Check(Enum):
    """An enumeration of all checks performed."""

    # fmt: off
    CONNECT = "1. Connect to the server"
    VERIFY = "2. Verify the server is an ODK Central server"
    AUTH = "3. Authenticate the provided credentials"
    PROJECT = "4. Check existence and access to the project, if provided"
    FORM_ID = "5. Check existence and access to the form ID within the project, if provided"
    INSTANCE_ID = "6. Check existence of the instance ID within the form, if provided"
    # fmt: on

    def _format_msg(self, status, width=13):

        return f"{status:<{width}}{self.value}"

    def print_success_msg(self) -> str:
        """Format the message for success."""
        print(self._format_msg("Success:"))

    def print_failure_msg(self) -> str:
        """Format the message for failure."""
        logger.warning("Check failed at step %s", self.value)
        print(self._format_msg("Failure:"))

    def print_skip_msg(self) -> str:
        """Format the message for a skip."""
        print(self._format_msg("Skip:"))


def check_connect_and_verify(client: CentralClient) -> bool:
    """Check the connection and verify the server is ODK Central."""
    try:
        resp = client.get_version()
        Check.CONNECT.print_success_msg()
        if resp.ok and all(i in resp.text for i in ("versions", "client", "server")):
            Check.VERIFY.print_success_msg()
        else:
            Check.VERIFY.print_failure_msg()
            print(
                f"-> Could not verify that this server is ODK Central by checking: {resp.url}"
            )
            return False
    except RequestException:
        Check.CONNECT.print_failure_msg()
        if client.url is None:
            print("-> centralpy is not configured with a URL.")
        else:
            print(
                "-> Check the internet connection and the spelling of the server URL:",
                client.url,
            )
        return False
    return True


def check_auth(client: CentralClient) -> bool:
    """Check that ODK Central can authenticate the provided credentials."""
    try:
        client.create_session_token()
        Check.AUTH.print_success_msg()
    except HTTPError:
        Check.AUTH.print_failure_msg()
        print(
            "-> ODK Central was unable to authenticate the provided credentials. Please verify email/password."
        )
        return False
    except AuthenticationError as err:
        Check.AUTH.print_failure_msg()
        print(err)
        return False
    return True


def check_project(client: CentralClient, project: Optional[str]) -> bool:
    """Check that the provided project is accessible."""
    project_listing = client.get_projects()
    projects = project_listing.get_projects()
    if project is None:
        Check.PROJECT.print_skip_msg()
        Check.FORM_ID.print_skip_msg()
        Check.INSTANCE_ID.print_skip_msg()
        print(
            "-> No project ID was provided. These are this user's projects "
            "accessible on ODK Central:"
        )
        project_listing.print_all()
        return True
    if project_listing.can_access_project(project):
        Check.PROJECT.print_success_msg()
        return True
    Check.PROJECT.print_failure_msg()
    if projects:
        print(
            f"-> No access for project {project}. These are this user's "
            "projects accessible on ODK Central:"
        )
        project_listing.print_all()
    else:
        print(
            "-> No projects are able to be accessed. Have an administrator "
            "add this user as a Project Manager."
        )
    return False


def check_form_id(client: CentralClient, project: str, form_id: Optional[str]) -> bool:
    """Check that the provided form ID is a form in the project."""
    form_listing = client.get_forms(project=project)
    forms = form_listing.get_forms()
    if form_id is None:
        Check.FORM_ID.print_skip_msg()
        Check.INSTANCE_ID.print_skip_msg()
        print("-> No form ID was provided. These forms were found on ODK Central:")
        form_listing.print_all()
        return True
    if form_listing.has_form_id(form_id):
        Check.FORM_ID.print_success_msg()
        return True
    Check.FORM_ID.print_failure_msg()
    if forms:
        print(
            f'-> Unable to find form ID "{form_id}" in project {project}. These forms were found:'
        )
        form_listing.print_all()
    else:
        print(f"-> No forms found in project {project}.")
    return False


def check_instance_id(
    client: CentralClient,
    project: str,
    form_id: str,
    instance_id: Optional[str],
) -> bool:
    """Check that the given instance ID is among submissions to a form."""
    submission_listing = client.get_submissions(project=project, form_id=form_id)
    submissions = submission_listing.get_submissions()
    if instance_id is None:
        Check.INSTANCE_ID.print_skip_msg()
        print("-> No instance ID was provided.")
        submission_listing.print_most_recent()
        return True
    if submission_listing.has_instance_id(instance_id):
        Check.INSTANCE_ID.print_success_msg()
        attachment_listing = client.get_attachments(project, form_id, instance_id)
        print("-> Report on attachments")
        attachment_listing.print_all()
        return True
    Check.INSTANCE_ID.print_failure_msg()
    if submissions:
        print(f'-> Unable to find instance ID "{instance_id}" in form ID {form_id}.')
        submission_listing.print_most_recent()
    else:
        print(f"-> No submissions found in form ID {form_id}.")
    return False


def check_connection(  # pylint: disable=too-many-return-statements,
    client: CentralClient,
    project: Optional[str],
    form_id: Optional[str],
    instance_id: Optional[str],
) -> bool:
    """
    Check the connection, configuration, and parameters for centralpy.

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
        logger.info("All checks through AUTH were successful, the rest skipped")
        return True
    if not has_project:
        return False
    has_form_id = check_form_id(client, project, form_id)
    if form_id is None:
        logger.info("All checks through PROJECT were successful, the rest skipped")
        return True
    if not has_form_id:
        return False
    has_instance_id = check_instance_id(client, project, form_id, instance_id)
    if instance_id is None:
        logger.info("All checks through FORM_ID were successful, the rest skipped")
        return True
    if not has_instance_id:
        return False
    logger.info("All checks were successfully performed")
    return True
