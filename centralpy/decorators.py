"""Custom decorators for centralpy source code."""
import functools
import sys

import click
import requests
from requests.exceptions import RequestException, HTTPError

from centralpy.errors import CentralpyError


def add_logging_options(func):
    """Add log_file and verbose options."""

    add_log_file = click.option(
        "--log-file",
        "-l",
        type=click.Path(dir_okay=False),
        default="./centralpy.log",
        show_default=True,
        help="Where to save logs.",
    )
    add_verbose = click.option(
        "--verbose",
        "-v",
        is_flag=True,
        help="Display logging messages to console. This cannot be enabled from a config file.",
    )
    return add_log_file(add_verbose(func))


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
                good, bad = check_segments(resp)
                print(
                    (
                        "Sorry, something went wrong. The server responded with a 404, "
                        "Resource not found. Verify the different components of this URL, "
                        "including the host and different path segments: "
                    )
                )
                print(resp.url)
                if good.request.path_url == "/":
                    print(
                        "While checking path segments of the original resource, "
                        "only the root server URL worked. Is this ODK Central?"
                    )
                elif good:
                    print(
                        "While checking path segments of the original "
                        "resource, was able to find a resource:"
                    )
                    print(f" - Status code 404 (bad) : {bad.request.url}")
                    print(
                        f" - Status code {good.status_code} (good): {good.request.url}"
                    )
                else:
                    print(
                        "While checking path segments of the original "
                        "resource, was unable to get a non-404 response"
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
        except RequestException as err:
            print(
                (
                    "Sorry, something went wrong. The request was unable to reach "
                    "the server. Try verifying the internet connection by navigating to "
                    "ODK Central in a browser, or by pinging the server. Also check the "
                    "spelling of the server URL:"
                )
            )
            print(err.request.url)
            sys.exit(1)
        else:
            return result

    return wrapper


def check_segments(resp):
    """Check the path segments to find a non-404 response."""
    auth_key = "Authorization"
    authorization = resp.request.headers.get(auth_key)
    auth_header = {}
    if authorization:
        auth_header[auth_key] = authorization
    host = resp.request.url[: -len(resp.request.path_url)]
    last_bad = resp.request.path_url
    last_resp = resp
    while last_bad:
        last_slash = last_bad.rfind("/")
        next_attempt = last_bad[:last_slash]
        next_resp = requests.get(f"{host}{next_attempt}", headers=auth_header)
        if next_resp.status_code != 404:
            return next_resp, last_resp
        last_bad = next_attempt
        last_resp = next_resp
    return None, last_resp
