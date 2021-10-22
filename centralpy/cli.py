"""CLI for PMA use cases."""
from io import BufferedReader, TextIOWrapper
import logging
from pathlib import Path
import pprint
import sys
from typing import Optional, Tuple

import click
from werkzeug.utils import secure_filename

from centralpy.__version__ import __version__
from centralpy import CentralClient
from centralpy.decorators import add_logging_options, handle_common_errors
from centralpy.errors import AuditReportError
from centralpy.loggers import setup_logging
from centralpy.use_cases import (
    check_connection,
    download_all_attachments,
    download_attachments_from_sequence,
    pull_csv_zip,
    keep_recent_zips,
    make_server_audit_report,
    push_submissions_and_attachments,
    repair_server_audits_from_report,
    upload_attachments_from_sequence,
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


# pylint: disable=too-many-arguments
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
def main(
    ctx,
    url: str,
    email: str,
    password: str,
    log_file: str,
    verbose: bool,
    config_file: TextIOWrapper,
):
    """
    Meet centralpy, an ODK Central command-line tool.

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
        str(centralpy_config.get("CENTRALPY_LOG_FILE")),
        bool(centralpy_config.get("CENTRALPY_VERBOSE")),
    )
    client = CentralClient(
        str(centralpy_config.get("CENTRALPY_URL")),
        str(centralpy_config.get("CENTRALPY_EMAIL")),
        str(centralpy_config.get("CENTRALPY_PASSWORD")),
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
    "--no-progress-bar",
    "-P",
    is_flag=True,
    help="Do not show progress bar for download.",
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
def pullcsv(
    ctx,
    project: int,
    form_id: str,
    csv_dir: Path,
    zip_dir: Path,
    no_attachments: bool,
    no_progress_bar: bool,
    keep: int,
):
    """
    Pull CSV data from ODK Central.

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
    pull_csv_zip(
        client, str(project), form_id, csv_dir, zip_dir, no_attachments, no_progress_bar
    )
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
    help="The attachment file to upload for the instance ID.",
)
@click.pass_context
def upload_attachments(
    ctx, project: int, form_id: str, instance_id: str, attachment: Tuple[BufferedReader]
):
    """
    Upload one or more attachments for the given submission.

    To pass multiple attachments, use -a multiple times.
    """
    client = ctx.obj["client"]
    logger.info(
        "Initiated attachment upload for project %s, form_id %s, instance_id %s, using %s",
        project,
        form_id,
        instance_id,
        [item.name for item in attachment],
    )
    upload_success = upload_attachments_from_sequence(
        client, str(project), form_id, instance_id, attachment
    )
    for success, stream in zip(upload_success, attachment):
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
        "Completed attachment upload for project %s, form_id %s, instance_id %s, using %s",
        project,
        form_id,
        instance_id,
        [item.name for item in attachment],
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
    multiple=True,
    help=(
        "The attachment file to download for the instance ID. "
        "If not given, then download all attachments."
    ),
)
@click.option(
    "--download-dir",
    "-d",
    type=click.Path(file_okay=False, path_type=Path),
    help=(
        "The directory to save audit files to. "
        "Default is a safe version of the instance ID as the directory."
    ),
)
@click.pass_context
def download_attachments(
    ctx,
    project: int,
    form_id: str,
    instance_id: str,
    attachment: Tuple[str],
    download_dir: Optional[Path],
):
    """
    Download attachments for the given submission.

    To download all attachments, do not specify -a.
    To specify multiple attachments, use -a multiple times.

    Use the check sub-command to see what attachments are available.
    """
    logger.info(
        "Download attachments initiated: project=%s, form_id=%s, instance_id=%s, "
        "attachment=%s, download_dir=%s",
        repr(project),
        repr(form_id),
        repr(instance_id),
        repr(attachment),
        repr(str(download_dir)),
    )
    client = ctx.obj["client"]
    if not download_dir:
        download_dir = Path(secure_filename(instance_id))
    if attachment:
        saved_at = download_attachments_from_sequence(
            client, str(project), form_id, instance_id, attachment, download_dir
        )
        for filename, path in zip(attachment, saved_at):
            if path:
                print(f'Saved attachment to "{path}"')
            else:
                print(
                    f'Unable to download "{filename}". '
                    "Perhaps it is misspelled or missing from the server?"
                )
    else:
        saved_at = download_all_attachments(
            client, str(project), form_id, instance_id, download_dir
        )
        for path in saved_at:
            print(f'Saved attachment to "{path}"')
    logger.info(
        "Download attachments completed: project=%s, form_id=%s, instance_id=%s, "
        "attachment=%s, download_dir=%s",
        repr(project),
        repr(form_id),
        repr(instance_id),
        repr(attachment),
        repr(str(download_dir)),
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
    "--report-file",
    "-r",
    required=True,
    type=click.Path(dir_okay=False, path_type=Path),
    help=(
        "Where to save results from checking audits in JSON format. "
        "This file is meant to be reused from check to check."
    ),
)
@click.option(
    "--audit-dir",
    "-a",
    required=True,
    type=click.Path(file_okay=False, path_type=Path),
    help="The directory to save audit files to",
)
@click.option(
    "--time",
    "-t",
    help=(
        "A relative time string, formatted as #h or #d with # is a number. "
        'Use "h" for hours and "d" for days. '
        "Check submissions in the last #h or #d."
    ),
)
@click.option(
    "--since-prev",
    "-s",
    is_flag=True,
    help=(
        "Check submissions received after the last check (from --report-file). "
        "If no --time option is given, then the code tries to filter by previous report time."
    ),
)
@click.pass_context
def check_server_audits(
    ctx,
    project: int,
    form_id: str,
    report_file: Path,
    audit_dir: Path,
    time: str,
    since_prev: bool,
):
    """
    Check audit files on ODK Central for correctness.

    This command saves bad audits to disk so they can be corrected.
    After correcting them, use repair-server-audits to upload back to
    ODK Central.
    """
    client = ctx.obj["client"]
    logger.info(
        "Check server audits initiated: project=%s, form_id=%s, report_file=%s, "
        "time=%s, since_prev=%s, audit_dir=%s",
        repr(project),
        repr(form_id),
        repr(str(report_file)),
        repr(time),
        repr(since_prev),
        repr(str(audit_dir)),
    )
    try:
        audit_report = make_server_audit_report(
            client,
            str(project),
            form_id,
            audit_dir,
            report_file,
            time,
            since_prev,
        )
        if audit_report.bad_audit:
            print(
                f"Audits checked: {audit_report.count_checked}. "
                f'Project {project}, form_id "{form_id}". '
                f"Malformed audits found: {len(audit_report.bad_audit)}."
            )
            for instance_id, result in audit_report.bad_audit.items():
                print(f"Instance ID: {instance_id}")
                for i, bad_record in result["bad_records"]:
                    print(f"-> Record {i:>4}: {bad_record}")
            print(f'All audits saved to directory "{audit_dir}"')
        else:
            print(
                f"Audits checked: {audit_report.count_checked}. "
                f'Project {project}, form_id "{form_id}". '
                "No malformed audits found."
            )
        print(f'Report of check-server-audits saved to "{report_file}".')
    except AuditReportError as e:
        print(f"{e.args[0]}")
    logger.info(
        "Check server audits completed: project=%s, form_id=%s, report_file=%s, "
        "time=%s, since_prev=%s, audit_dir=%s",
        repr(project),
        repr(form_id),
        repr(str(report_file)),
        repr(time),
        repr(since_prev),
        repr(str(audit_dir)),
    )


@main.command()
@handle_common_errors
@click.option(
    "--report-file",
    "-r",
    required=True,
    type=click.Path(dir_okay=False, path_type=Path, exists=True),
    help=(
        "The JSON file saved from check-server-audits. "
        "This file contains metadata about where to find instances."
    ),
)
@click.pass_context
def repair_server_audits(
    ctx,
    report_file: Path,
):
    """
    Repair audit files on ODK Central by uploading corrected audits.

    This is meant to be used after running check-server-audits.
    """
    client = ctx.obj["client"]
    logger.info(
        "Repair server audits initiated: report_file=%s",
        repr(str(report_file)),
    )
    audit_report = repair_server_audits_from_report(client, report_file)
    print(
        f"Count of repaired audits: {audit_report.count_checked}.",
        f"Remaining bad audits: {len(audit_report.bad_audit)}",
    )
    logger.info(
        "Repair server audits completed: report_file=%s",
        repr(str(report_file)),
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
def check(ctx, project: int, form_id: str, instance_id: str):  # noqa: D301
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
