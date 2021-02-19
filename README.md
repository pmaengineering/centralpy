# A Python client for ODK Central

ODK Central has an [API][api], and this Python package interacts with it. The use cases in this package were written to support PMA data management purposes, but the package can be extended for other use cases as well.

# Installation

First, make sure Python3 (at least version 3.6) is installed. 

Use `pip` to install this package with

```
python3 -m pip install centralpy
```

From here, the program runs by using either the installed script, e.g.

```
centralpy --help
```

or, by invoking the module with

```
python3 -m centralpy --help
```

FYI: this package's dependencies are
- [`requests`][requests] for communicating with ODK Central
- [`click`][click] for composing the command-line interface

[api]: https://odkcentral.docs.apiary.io/#
[requests]: https://requests.readthedocs.io/en/master/
[click]: https://click.palletsprojects.com/en/master/

# Usage

The main command `centralpy` does not do anything by itself. It has its own options to configure the program and then delegate to its subcommands.

The options for the main command `centralpy` are

Option | Description 
--- | ---
  --url TEXT              | The URL for the ODK Central server
  --email TEXT            | An ODK Central user email
  --password TEXT         | The password for the account
  --log-file FILE         | Where to save logs.  (default: ./centralpy.log)
  --verbose               | Display logging messages to console. This cannot be enabled from a config file.
  --config-file FILENAME  | A configuration file with KEY=VALUE defined (one per line). Keys should be formatted as CENTRAL_***.
  --help                  | Show this message and exit.

There are then four subcommands. 

- [`pullcsv`](#subcommand-pullcsv)
- [`push`](#subcommand-push)
- [`config`](#subcommand-config)
- [`version`](#subcommand-version)

## Subcommand: pullcsv

This subcommand downloads the CSV zip file and extracts data CSVs. The zip file is saved with a timestamp in the filename in order to assist in deleting old zip files (see the `--keep` option).

An easy way to get the project ID (a number) and the XForm ID is to navigate to the form on ODK Central, and then examine the URL.

The options for `pullcsv` are

Option | Description 
--- | ---
  --project INTEGER    | The numeric ID of the project. ODK Central assigns this ID when the project is created.  (required)
  --form-id TEXT       | The form ID (a string), usually defined in the XLSForm settings. This is a unique identifier for an ODK form. (required)
  --csv-dir DIRECTORY  | The directory to export CSV files to  (default: ./)
  --zip-dir DIRECTORY  | The directory to save the downloaded zip to  (default: ./)
  --keep INTEGER       | The number of zip files to keep in the zip directory, keeping the most recent. The number must be 1 or larger for anything to happen. (default: -1)
  --help               | Show this message and exit.

## Subcommand: push

This subcommand crawls through a local directory looking for XML files to upload. The form ID is autodetected from the XML.

The options for `push` are

Option | Description 
--- | ---
  --project INTEGER      | The numeric ID of the project  (required)
  --local-dir DIRECTORY  | The directory to push uploads from  (default: ./)
  --help                 | Show this message and exit.

## Subcommand: config

This subcommand prints out the configuration that the main command, `centralpy` uses

## Subcommand: version

This subcommand prints out centralpy's version.

*NOTE:* The logs generated from `cli.py` also include the version number.

# Example usage

How to
- Pull CSV data
- Save CSV data and zip files to different directories
- Keep the most recent 7 zip files

```
# First on one line
centralpy --url "https://central.example.com" --email "manager@example.com" --password "password1234" --verbose pullcsv --project 1 --form-id MY_FORM_ID --csv-dir /path/to/csv/dir --zip-dir /path/to/zip/dir --keep 7
# Then the same command on multiple lines
centralpy \
--url "https://central.example.com" \
--email "manager@example.com" \
--password "password1234" \
--verbose \
pullcsv \
--project 1 \
--form-id MY_FORM_ID \
--csv-dir /path/to/csv/dir \
--zip-dir /path/to/zip/dir \
--keep 7
```

How to
- Do the same as the above using a log file

```
# First on one line
centralpy --config-file /path/to/config.txt --verbose pullcsv --project 1 --form-id MY_FORM_ID --csv-dir /path/to/csv/dir --zip-dir /path/to/zip/dir --keep 7
# Then the same command on multiple lines
centralpy \
--config-file /path/to/config.txt \
--verbose \
pullcsv \
--project 1 \
--form-id MY_FORM_ID \
--csv-dir /path/to/csv/dir \
--zip-dir /path/to/zip/dir \
--keep 7
```

How to
- Push XML files to ODK Central

```
# First on one line
centralpy --url "https://odkcentral.example.com" --email "manager@example.com" --password "password1234" push --project 1 --local-dir /path/to/dir
# Then the same command on multiple lines
centralpy \
--url "https://odkcentral.example.com" \
--email "manager@example.com" \
--password "password1234" \
push \
--project 1 \
--local-dir /path/to/dir
```

# An example config file

A config file can be specified for the main command, `centralpy`. The following demonstrates the contents of an example config file:

```
CENTRAL_URL=https://odkcentral.example.com
CENTRAL_EMAIL=manager@example.com
CENTRAL_PASSWORD=password1234
CENTRAL_LOG_FILE=centralpy.log
```

# Develop

- Create a virtual environment `python3 -m venv env/ --prompt centralpy`
- Activate it `source env/bin/activate`
- Install `pip-tools` with `python3 -m pip install pip-tools`
- Clone this repository
- Download all developer packages: `pip-sync requirements.txt requirements-dev.txt`

# Bugs

Submit bug reports on the Github repository's issue tracker at [https://github.com/pmaengineering/centralpy/issues][issues]. Or, email the maintainer at jpringleBEAR@jhu.edu (minus the BEAR).

[issues]: https://github.com/pmaengineering/centralpy/issues