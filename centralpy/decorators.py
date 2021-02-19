"""Custom decorators for centralpy source code."""
import functools
import sys

from requests.exceptions import HTTPError

from centralpy.errors import CentralpyError


def handle_common_errors(func):
    """Handle common errors from interacting with ODK Central."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
        except CentralpyError as err:
            print(err)
            sys.exit(1)
        except HTTPError as err:
            resp = err.response
            if resp.status_code == 401:
                print(
                    (
                        "Sorry, something went wrong. ODK Central did not accept the provided "
                        f"credentials. ODK Central's message is {resp.text}."
                    )
                )
            elif resp.status_code == 403:
                print(
                    (
                        "Sorry, something went wrong. The authenticated user does not have "
                        "permission to perform the requested action. Verify the web user "
                        "is added to the correct project and has the Project Manager role "
                        "on that project. "
                        f"ODK Central's message is {resp.text}."
                    )
                )
            elif resp.status_code == 404:
                print(
                    (
                        "Sorry, something went wrong. The server responded with a 404, "
                        "Resource not found. Verify the different components of this URL, "
                        "including the host and different path segments: "
                        f"{resp.url}"
                    )
                )
            else:
                print(
                    (
                        "Sorry, something went wrong. In response to a request, ODK Central "
                        f"responded with the error code {resp.status_code}. "
                        f"ODK Central's message is {resp.text}. "
                        "Hopefully that helps!"
                    )
                )
            sys.exit(1)
        except ConnectionError:
            print(
                (
                    "Sorry, something went wrong. The request was unable to reach "
                    "the server. Try verifying the internet connection by navigating to "
                    "ODK Central in a browser, or by pinging the server."
                )
            )
            sys.exit(1)
        else:
            return result

    return wrapper
