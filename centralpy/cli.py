import logging
from pathlib import Path
import pprint
import sys

import click
from requests.exceptions import HTTPError

from centralpy.__version__ import __version__
from centralpy import CentralClient
from centralpy.pull_csv_zip import pull_csv_zip, keep_recent_zips


logger = logging.getLogger(__name__)


@click.group()
@click.option("--url", type=str, help="The URL for the ODK Central server")
@click.option("--email", type=str, help="An ODK Central user email")
@click.option("--password", type=str, help="The password for the account")
@click.option(
    "--log-file",
    type=click.Path(dir_okay=False),
    help="Where to save logs. If not provided, then logs are not saved.",
)
@click.option(
    "--verbose",
    is_flag=True,
    help="Display logging messages to console. This cannot be enabled from a config file.",
)
@click.option(
    "--config-file",
    type=click.File(),
    help="A configuration file with KEY=VALUE defined (one per line). Keys should be formatted as CENTRAL_***.",
)
@click.pass_context
def main(ctx, url, email, password, log_file, verbose, config_file):
    """This is centralpy, an ODK Central command-line tool.

    Configure centralpy with a URL and credentials using command-line
    parameters or from a config file. Values passed as parameters on the
    command line take precedence over values in a config file.
    """
    if ctx.invoked_subcommand == "version":
        return
    config = get_centralpy_config(
        config_file,
        CENTRAL_URL=url,
        CENTRAL_EMAIL=email,
        CENTRAL_PASSWORD=password,
        CENTRAL_LOG_FILE=log_file,
        CENTRAL_VERBOSE=verbose,
    )
    ctx.ensure_object(dict)
    ctx.obj["config"] = config
    if ctx.invoked_subcommand == "config":
        return
    setup_logging(config.get("CENTRAL_LOG_FILE"), config.get("CENTRAL_VERBOSE"))
    try:
        client = CentralClient(
            config["CENTRAL_URL"],
            config["CENTRAL_EMAIL"],
            config["CENTRAL_PASSWORD"],
        )
        ctx.obj["client"] = client
    except KeyError as err:
        print(
            f"Sorry, unable to create an ODK Central client because of missing information: {err!s}."
        )
        print(
            "Try adding this information to a config file or pass it as a command-line option."
        )
        print('Type "centralpy --help" for more information.')
        sys.exit(1)


@main.command()
@click.option(
    "--project",
    required=True,
    type=int,
    help="The numeric ID of the project. ODK Central assigns this ID when the project is created.",
)
@click.option(
    "--form-id",
    required=True,
    type=str,
    help="The form ID (a string), usually defined in the XLSForm settings. This is a unique identifier for an ODK form.",
)
@click.option(
    "--csv-dir",
    required=True,
    type=click.Path(file_okay=False),
    help="The directory to export CSV files to",
)
@click.option(
    "--zip-dir",
    required=True,
    type=click.Path(file_okay=False),
    help="The directory to save the downloaded zip to",
)
@click.option(
    "--keep",
    default=0,
    help="The number of zip files to keep in the zip directory, keeping the most recent. The number must be larger than 0 for anything to happen.",
)
@click.pass_context
def pullcsv(ctx, project, form_id, csv_dir, zip_dir, keep):
    """Pull CSV data from ODK Central.

    An easy way to get the project ID (a number) and the XForm ID is to
    navigate to the form on ODK Central, and then examine the URL.
    """
    client = ctx.obj["client"]
    try:
        logger.info(
            "CSV pull initiated: URL %s, project %s, form_id %s",
            client.url,
            project,
            form_id,
        )
        pull_csv_zip(client, str(project), form_id, Path(csv_dir), Path(zip_dir))
        keep_recent_zips(keep, form_id, Path(zip_dir))
        logger.info(
            "CSV pull completed: URL %s, project %s, form_id %s",
            client.url,
            project,
            form_id,
        )
    except HTTPError as err:
        resp = err.response
        if resp.status_code == 401:
            print(
                (
                    "Sorry, something went wrong. ODK Central did not accept the provided credentials. "
                    f"ODK Central's message is {resp.text}."
                )
            )
        elif resp.status_code == 404:
            print(
                (
                    "Sorry, something went wrong. The server responded with a 404, Resource not found. "
                    "ODK Central should not do that. "
                    f'The provided ODK Central URL is "{client.url}". Is that correct?'
                )
            )
        else:
            print(
                (
                    "Sorry, something went wrong. In response to the request for a CSV zip, ODK Central "
                    f"responded with the error code {resp.status_code}. "
                    f"ODK Central's message is {resp.text}. "
                    "Hopefully that helps!"
                )
            )
        sys.exit(1)


@main.command()
@click.option(
    "--project", required=True, type=int, help="The numeric ID of the project"
)
@click.option(
    "--local-dir",
    required=True,
    type=click.Path(file_okay=False),
    help="The directory to push uploads from",
)
@click.pass_context
def push(ctx, project, local_dir):
    """Push ODK submissions to ODK Central."""


@main.command()
@click.pass_context
def config(ctx):
    """Show the configuration that centralpy is using."""
    pprint.pprint(ctx.obj["config"])


@main.command()
def version():
    """Show centralpy version and exit."""
    print(f"centralpy v{__version__}")


def get_centralpy_config(config_file, **kwargs):
    config = {}
    if config_file:
        for line in config_file:
            if "=" in line:
                key, value = line.split("=", 1)
                config[key.strip()] = value.strip()
    for key, value in kwargs.items():
        if key.startswith("CENTRAL_") and value is not None:
            config[key] = value
    filtered = {k: v for k, v in config.items() if k.startswith("CENTRAL_")}
    return filtered


def setup_logging(log_file, verbose):
    centralpy_logger = logging.getLogger("centralpy")
    centralpy_logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    if verbose:
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(logging.NOTSET)
        stream_handler.setFormatter(formatter)
        centralpy_logger.addHandler(stream_handler)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.NOTSET)
        file_handler.setFormatter(formatter)
        centralpy_logger.addHandler(file_handler)
