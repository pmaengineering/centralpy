"""CLI for PMA use cases."""
import logging
from pathlib import Path
import pprint

import click

from centralpy.__version__ import __version__
from centralpy import CentralClient
from centralpy.decorators import handle_common_errors
from centralpy.use_cases import (
    pull_csv_zip,
    keep_recent_zips,
    push_submissions_and_attachments,
)


logger = logging.getLogger(__name__ + ".v" + __version__)


@click.group()
@click.option("--url", type=str, help="The URL for the ODK Central server")
@click.option("--email", type=str, help="An ODK Central user email")
@click.option("--password", type=str, help="The password for the account")
@click.option(
    "--log-file",
    type=click.Path(dir_okay=False),
    default="./centralpy.log",
    show_default=True,
    help="Where to save logs.",
)
@click.option(
    "--verbose",
    is_flag=True,
    help="Display logging messages to console. This cannot be enabled from a config file.",
)
@click.option(
    "--config-file",
    type=click.File(),
    help=(
        "A configuration file with KEY=VALUE defined (one per line). "
        "Keys should be formatted as CENTRAL_***."
    ),
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
    # pylint: disable=redefined-outer-name
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
    client = CentralClient(
        config.get("CENTRAL_URL"),
        config.get("CENTRAL_EMAIL"),
        config.get("CENTRAL_PASSWORD"),
    )
    ctx.obj["client"] = client


@main.command()
@handle_common_errors
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
    help=(
        "The form ID (a string), usually defined in the XLSForm settings. "
        "This is a unique identifier for an ODK form."
    ),
)
@click.option(
    "--csv-dir",
    default="./",
    show_default=True,
    type=click.Path(file_okay=False),
    help="The directory to export CSV files to",
)
@click.option(
    "--zip-dir",
    default="./",
    show_default=True,
    type=click.Path(file_okay=False),
    help="The directory to save the downloaded zip to",
)
@click.option(
    "--keep",
    default=-1,
    show_default=True,
    help=(
        "The number of zip files to keep in the zip directory, keeping the "
        "most recent. The number must be 1 or larger for any old files to be "
        "deleted."
    ),
)
@click.pass_context
def pullcsv(ctx, project, form_id, csv_dir, zip_dir, keep):
    """Pull CSV data from ODK Central.

    An easy way to get the project ID (a number) and the XForm ID is to
    navigate to the form on ODK Central, and then examine the URL.
    """
    client = ctx.obj["client"]
    logger.info(
        "CSV pull initiated: URL %s, project %s, form_id %s",
        client.url,
        project,
        form_id,
    )
    pull_csv_zip(client, str(project), form_id, Path(csv_dir), Path(zip_dir))
    print(
        f"Successfully saved zip file to {zip_dir} and extracted all CSV files to {csv_dir}"
    )
    if keep > 0:
        keep_recent_zips(keep, form_id, Path(zip_dir))
        print(f"Successfully ensured at most {keep} zip files are kept")
    logger.info(
        "CSV pull completed: URL %s, project %s, form_id %s",
        client.url,
        project,
        form_id,
    )


@main.command()
@handle_common_errors
@click.option(
    "--project", required=True, type=int, help="The numeric ID of the project"
)
@click.option(
    "--local-dir",
    type=click.Path(file_okay=False),
    default="./",
    show_default=True,
    help="The directory to push uploads from",
)
@click.pass_context
def push(ctx, project, local_dir):
    """Push ODK submissions to ODK Central."""
    client = ctx.obj["client"]
    logger.info(
        "Submission push initiated to URL %s, project %s, from local directory %s",
        client.url,
        project,
        local_dir,
    )
    push_submissions_and_attachments(client, str(project), Path(local_dir))
    logger.info(
        "Submission push completed to URL %s, project %s, from local directory %s",
        client.url,
        project,
        local_dir,
    )


@main.command()
@click.pass_context
def config(ctx):
    """Show the configuration that centralpy is using."""
    pprint.pprint(ctx.obj["config"])


@main.command()
def version():
    """Show centralpy version and exit."""
    print(f"centralpy v{__version__}")


def get_centralpy_config(config_file: click.File, **kwargs) -> dict:
    """Combine configuration from a file and from keyword arguments."""
    # pylint: disable=redefined-outer-name
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


def setup_logging(log_file: click.File, verbose: bool) -> None:
    """Set up logging for centralpy."""
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
