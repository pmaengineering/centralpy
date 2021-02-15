import logging

import click

from centralpy import CentralClient
from centralpy.__version__ import __version__


@click.group()
@click.option('--server-url', type=str, help="The URL for the ODK Central server")
@click.option('--email', type=str, help="An ODK Central user email")
@click.option('--password', type=str, help="The password for the account")
@click.option('--log-file', type=click.Path(dir_okay=False), help="Where to save logs. If not provided, then logs are not saved.")
@click.option('--verbose', is_flag=True, help="Display logging messages to console")
@click.option('--config', type=click.File(), help="A configuration file with KEY=VALUE defined. Keys should be formatted as CENTRAL_***")
@click.pass_context
def main(ctx, server_url, email, password, log_file, config, verbose):
    """Configure the Central command-line tool with server URL and credentials.
    
    Values passed as parameters take precedence over values in a config file.
    """
    config_dict = {}
    if config:
        config_dict = parse_config(config)
    if server_url:
        config_dict['CENTRAL_URL'] = server_url
    if email:
        config_dict['CENTRAL_EMAIL'] = email
    if password:
        config_dict['CENTRAL_PASSWORD'] = password
    if log_file:
        config_dict['CENTRAL_LOG_FILE'] = log_file
    ctx.ensure_object(dict)
    client = CentralClient(
        config_dict.get('CENTRAL_URL'),
        config_dict.get('CENTRAL_EMAIL'),
        config_dict.get('CENTRAL_PASSWORD'),
    )
    ctx.obj['client'] = client
    setup_logging(config_dict.get("CENTRAL_LOG_FILE"))


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


def parse_config(config_file):
    return {
        k.strip(): v.strip() for k, v in (line.split("=", 1) for line in config_file if "=" in line)
    }

def setup_logging(log_file):
    logging.basicConfig(filename=log_file, level=logging.INFO)