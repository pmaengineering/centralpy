"""CLI for PMA use cases."""
from io import BufferedReader, TextIOWrapper
import logging
from pathlib import Path
import pprint
import sys
from typing import Tuple

import click

from centralpy.__version__ import __version__
from centralpy import CentralClient
from centralpy.decorators import add_logging_options, handle_common_errors
from centralpy.loggers import setup_logging
from centralpy.use_cases import (
    check_connection,
    pull_csv_zip,
    keep_recent_zips,
    push_submissions_and_attachments,
    update_attachments_from_sequence,
)


logger = logging.getLogger(__name__ + ".v" + __version__)


PROJECT_HELP = "The numeric ID of the project. ODK Central assigns this ID when the project is created."
FORM_ID_HELP = (
    "The form ID (a string), usually defined in the XLSForm settings. This is a unique "
    "identifier for an ODK form."
)
INSTANCE_ID_HELP = (
    "An instance ID, found in the metadata for a submission. This is a unique identifier for an "
    "ODK submission to a form."
)


@click.group(invoke_without_command=True)
@click.option(
    "--url",
    "-u",
    help="The URL for the ODK Central server",
)
@click.option(
    "--email",
    "-e",
    help="An ODK Central user email",
)
@click.option(
    "--password",
    "-p",
    help="The password for the account",
)
@add_logging_options
@click.option(
    "--config-file",
    "-c",
    type=click.File(),
    help=(
        "A configuration file with KEY=VALUE defined (one per line). "
        "Keys should be formatted as CENTRALPY_***."
    ),
)
@click.pass_context
def main(  # pylint: disable=too-many-arguments
    ctx,
    url: str,
    email: str,
    password: str,
    log_file: str,
    verbose: bool,
    config_file: TextIOWrapper,
):
    """
    This is centralpy, an ODK Central command-line tool.

    Configure centralpy with a URL and credentials using command-line
    parameters or from a config file. Values passed as parameters on the
    command line take precedence over values in a config file.
    """
    if ctx.invoked_subcommand is None:
        print(ctx.get_help())
        return
    if ctx.invoked_subcommand == "version":
        return
    centralpy_config = get_centralpy_config(
        config_file,
        CENTRALPY_URL=url,
        CENTRALPY_EMAIL=email,
        CENTRALPY_PASSWORD=password,
        CENTRALPY_LOG_FILE=log_file,
        CENTRALPY_VERBOSE=verbose,
    )
    ctx.ensure_object(dict)
    ctx.obj["config"] = centralpy_config
    if ctx.invoked_subcommand == "config":
        return
    setup_logging(
        centralpy_config.get("CENTRALPY_LOG_FILE"),
        centralpy_config.get("CENTRALPY_VERBOSE"),
    )
    client = CentralClient(
        centralpy_config.get("CENTRALPY_URL"),
        centralpy_config.get("CENTRALPY_EMAIL"),
        centralpy_config.get("CENTRALPY_PASSWORD"),
    )
    ctx.obj["client"] = client


@main.command()
@handle_common_errors
@click.option(
    "--project",
    "-p",
    required=True,
    type=int,
    help=PROJECT_HELP,
)
@click.option(
    "--form-id",
    "-f",
    required=True,
    help=FORM_ID_HELP,
)
@click.option(
    "--csv-dir",
    "-c",
    default="./",
    show_default=True,
    type=click.Path(file_okay=False, path_type=Path),
    help="The directory to export CSV files to",
)
@click.option(
    "--zip-dir",
    "-z",
    default="./",
    show_default=True,
    type=click.Path(file_okay=False, path_type=Path),
    help="The directory to save the downloaded zip to",
)
@click.option(
    "--no-attachments",
    "-A",
    is_flag=True,
    help=(
        "If this flag is supplied, then the CSV zip will be downloaded "
        "without attachments."
    ),
)
@click.option(
    "--keep",
    "-k",
    type=int,
    help=(
        "The number of zip files to keep in the zip directory, keeping the "
        "most recent. The number must be 1 or larger for any old files to be "
        "deleted."
    ),
)
@click.pass_context
def pullcsv(  # pylint: disable=too-many-arguments
    ctx,
    project: int,
    form_id: str,
    csv_dir: Path,
    zip_dir: Path,
    no_attachments: bool,
    keep: int,
):
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
    pull_csv_zip(client, str(project), form_id, csv_dir, zip_dir, no_attachments)
    print(
        f"Successfully saved zip file to {zip_dir} and extracted all CSV files to {csv_dir}"
    )
    if keep is not None and keep > 0:
        keep_recent_zips(keep, form_id, zip_dir)
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
    "--project",
    "-p",
    required=True,
    type=int,
    help=PROJECT_HELP,
)
@click.option(
    "--local-dir",
    "-l",
    type=click.Path(file_okay=False, path_type=Path),
    default="./",
    show_default=True,
    help="The directory to push uploads from",
)
@click.pass_context
def push(ctx, project: int, local_dir: Path):
    """
    Push ODK submissions to ODK Central.

    Centralpy crawls through all subfolders looking for XML files to upload.

    Centralpy expects there to be no more than one XML file per subfolder,
    which is how instances are saved on the phone by ODK Collect.
    """
    client = ctx.obj["client"]
    logger.info(
        "Submission push initiated to URL %s, project %s, from local directory %s",
        client.url,
        project,
        local_dir,
    )
    push_submissions_and_attachments(client, str(project), local_dir)
    logger.info(
        "Submission push completed to URL %s, project %s, from local directory %s",
        client.url,
        project,
        local_dir,
    )


@main.command()
@handle_common_errors
@click.option(
    "--project",
    "-p",
    required=True,
    type=int,
    help=PROJECT_HELP,
)
@click.option(
    "--form-id",
    "-f",
    required=True,
    help=FORM_ID_HELP,
)
@click.option(
    "--instance-id",
    "-i",
    required=True,
    help=INSTANCE_ID_HELP,
)
@click.option(
    "--attachment",
    "-a",
    required=True,
    multiple=True,
    type=click.File(mode="rb"),
    help="The attachment file to update for the instance ID.",
)
@click.pass_context
def update_attachments(
    ctx, project: int, form_id: str, instance_id: str, attachment: Tuple[BufferedReader]
):
    """
    Update one or more attachments for the given submission.

    To pass multiple attachments, use -a multiple times.
    """
    client = ctx.obj["client"]
    logger.info(
        "Initiated attachment update for project %s, form_id %s, instance_id %s, using %s",
        project,
        form_id,
        instance_id,
        [item.name for item in attachment],
    )
    success = update_attachments_from_sequence(
        client, str(project), form_id, instance_id, attachment
    )
    for success, stream in zip(success, attachment):
        if success:
            print(
                f'-> Successfully uploaded "{stream.name}" to instance "{instance_id}"'
            )
        else:
            print(
                f'-> Unable to upload "{stream.name}" to instance "{instance_id}".',
                'Try the "check" subcommand for more information about this instance.',
            )
    logger.info(
        "Completed attachment update for project %s, form_id %s, instance_id %s, using %s",
        project,
        form_id,
        instance_id,
        [item.name for item in attachment],
    )


@main.command()
@click.option(
    "--project",
    "-p",
    type=int,
    help=PROJECT_HELP,
)
@click.option(
    "--form-id",
    "-f",
    help=FORM_ID_HELP,
)
@click.option(
    "--instance-id",
    "-i",
    help=INSTANCE_ID_HELP,
)
@click.pass_context
def check(ctx, project: int, form_id: str, instance_id: str):
    """
    Check the connection, configuration, and parameters for centralpy.

    These checks are performed in order, checking that centralpy can

    \b
    1. Connect to the server
    2. Verify the server is an ODK Central server
    3. Authenticate the provided credentials
    4. Check existence and access to the project, if provided
    5. Check existence and access to the form ID within the project, if provided
    6. Check existence of the instance ID within the form, if provided

    If any of the checks fail, then the remaining checks are not performed.

    TIP: If a project is not provided, but the credentials are valid, then
    centralpy will show which projects are accessible for the user. Likewise,
    if there are valid credentials and a valid project, then centralpy will
    show which form IDs are accessible for the user.
    """
    client = ctx.obj["client"]
    logger.info(
        "Connection / configuration / parameter check initiated: "
        "URL %s, project %s, form_id %s, instance_id %s",
        client.url,
        project,
        form_id,
        instance_id,
    )
    result = check_connection(
        client, None if project is None else str(project), form_id, instance_id
    )
    logger.info(
        "Connection / configuration / parameter check completed: "
        "URL %s, project %s, form_id %s, instance_id %s",
        client.url,
        project,
        form_id,
        instance_id,
    )
    if not result:
        sys.exit(1)


@main.command()
@click.pass_context
def config(ctx):
    """Show the configuration that centralpy is using."""
    pprint.pprint(ctx.obj["config"])


@main.command()
def version():
    """Show centralpy version and exit."""
    print(f"centralpy v{__version__}")


def get_centralpy_config(config_file: TextIOWrapper, **kwargs) -> dict:
    """Combine configuration from a file and from keyword arguments."""
    centralpy_config = {}
    if config_file:
        for line in config_file:
            if "=" in line:
                key, value = line.split("=", 1)
                if key.strip().startswith("CENTRALPY_"):
                    centralpy_config[key.strip()] = value.strip()
        if not centralpy_config:
            logger.warning(
                'Trying to use config file "%s" but found no keys named "CENTRALPY_***"',
                config_file.name,
            )
    for key, value in kwargs.items():
        if key.startswith("CENTRALPY_") and value is not None:
            centralpy_config[key] = value
    filtered = {k: v for k, v in centralpy_config.items() if k.startswith("CENTRALPY_")}
    return filtered
