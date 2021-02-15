import logging
import sys

import click

from centralpy import CentralClient
from centralpy.__version__ import __version__


logger = logging.getLogger(__name__)


@click.group()
@click.option('--url', type=str, help="The URL for the ODK Central server")
@click.option('--email', type=str, help="An ODK Central user email")
@click.option('--password', type=str, help="The password for the account")
@click.option('--log-file', type=click.Path(dir_okay=False), help="Where to save logs. If not provided, then logs are not saved.")
@click.option('--verbose', is_flag=True, help="Display logging messages to console. This cannot be enabled from a config file.")
@click.option('--config-file', type=click.File(), help="A configuration file with KEY=VALUE defined (one per line). Keys should be formatted as CENTRAL_***.")
@click.pass_context
def main(ctx, url, email, password, log_file, verbose, config_file):
    """This is centralpy, an ODK Central command-line tool.

    Configure centralpy with a URL and credentials using command-line
    parameters or from a config file. Values passed as parameters on the
    command line take precedence over values in a config file.
    """
    if ctx.invoked_subcommand == 'version':
        return
    config = get_centralpy_config(
        config_file,
        CENTRAL_URL=url,
        CENTRAL_EMAIL=email,
        CENTRAL_PASSWORD=password,
        CENTRAL_LOG_FILE=log_file,
        CENTRAL_VERBOSE=verbose,
    )
    setup_logging(config.get("CENTRAL_LOG_FILE"), config.get("CENTRAL_VERBOSE"))
    try:
        client = CentralClient(
            config['CENTRAL_URL'],
            config['CENTRAL_EMAIL'],
            config['CENTRAL_PASSWORD'],
        )
        ctx.ensure_object(dict)
        ctx.obj['client'] = client
    except KeyError as err:
        print(f'Sorry, unable to create an ODK Central client because of missing information: {err!s}.')
        print('Try adding this information to a config file or pass it as a command-line option.')
        print('Type "centralpy --help" for more.')
        sys.exit(1)



@main.command()
@click.option('--project', required=True, type=int, help="The numeric ID of the project")
@click.option('--xform-id', required=True, type=str, help="The Xform ID (a string)")
@click.option('--export-dir', required=True, type=click.Path(file_okay=False), help="The directory to export CSV files to")
@click.option('--storage-dir', required=True, type=click.Path(file_okay=False), help="The directory to save the downloaded zip to")
@click.pass_context
def pull(ctx, project, xform_id, export_dir, storage_dir):
    """Pull CSV data from ODK Central."""
    pass


@main.command()
@click.option('--project', required=True, type=int, help="The numeric ID of the project")
@click.option('--local-directory', required=True, type=click.Path(file_okay=False), help="The directory to push uploads from")
@click.pass_context
def push(ctx, project, local_directory):
    """Push ODK submissions to ODK Central."""


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
    return config


def setup_logging(log_file, verbose):
    centralpy_logger = logging.getLogger('centralpy')
    centralpy_logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter(fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
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
    if verbose or log_file:
        logger.info("Logging is enabled!")