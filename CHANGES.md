# v0.6.0, 21 October 2021
## Breaking changes
* The `update-attachments` is changed to `upload-attachments` in order to pair with `download-attachments`.
## What's new
* Added `download-attachments` subcommand in order to download attachments for a single instance.
* Added `check-server-audits` and `repair-server-audits` to deal with the problem of malformed audit files.
## What's fixed
* Fixed an error when running `pullcsv` with `--keep` option that caused a crash.

# v0.5.2, 7 October 2021
## What's new
* Display a progress bar when downloading CSV zip
* Added `--no-progress-bar/-P` option to `pullcsv` command in order not to display progress bar
## What's changed
* Centralpy streams CSV zip downloads to conserve memory rather than store everything in memory

# v0.5.0, 27 September 2021
## Breaking changes
* Config file keys must start with `CENTRALPY_` instead of `CENTRAL_`
* Requires click >= 8.0.0
## What's new
* Added installed command `check-audits`, also reachable from `python -m centralpy.check_audits`.
* Added `update-attachments` subcommand
* Added `--instance-id` option to `check` subcommand
* Added single letter option spellings for all options, e.g. `-f` for `--form-id`.
## What's changed
* `--keep` option of `pullcsv` no longer has default of -1 to create less confusion. Does not change usage. Only observable change is in the help text.
* The command `centralpy` by itself now shows the help message rather than nothing.
* Better messaging on the `check` subcommand if no URL is given.

# v0.4.0, 27 July 2021
## What's new
* Added the `--no-attachments` option to `pullcsv`
* Added detail to the logs to say if attachments were downloaded or not

# v0.3.0, 5 March 2021
## What's new
* Added the `check` subcommand
* Add messaging on 404 responses to help find the cause (a common event due to typos)
* Add French translation to the README

# v0.2.0, 19 February 2021
## What's new
* Implemented `pullcsv` and `push` subcommands
* Added informational `version` and `config` subcommands
* By default, logs are saved in a file called "centralpy.log" in the current working directory.
* Improved documentation on the README
* Uploaded to PyPI, i.e. this is now pip-installable

# v0.1.0, 11 February 2021
## What's new
* This is the initial release 🎉
* Command-line interface for scripting
