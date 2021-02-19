"""A module for the use case of pushing submissions and their attachments."""
from collections import Counter
import logging
from pathlib import Path
from typing import Iterable, Optional
import xml.etree.ElementTree as ET

from requests.exceptions import HTTPError

from centralpy.client import CentralClient


logger = logging.getLogger(__name__)


def push_submissions_and_attachments(
    client: CentralClient, project: str, local_dir: Path
):
    """Push submissions and attachments to ODK Central.

    This routine expects that individual XML files are enclosed in individual
    folders. Attachments should be alongside the XML files that they are
    associated with.
    """
    found_xml = list(local_dir.glob("**/*.xml"))
    path_counter = Counter(path.parent for path in found_xml)
    logger.info(
        "Count of XML files discovered in root folder %s: %d", local_dir, len(found_xml)
    )
    multiples = {k: v for k, v in path_counter.items() if v > 1}
    if multiples:
        multiples_count = sum(multiples.values())
        logger.warning(
            "Count of XML files skipped due to being in a common folder: %d",
            multiples_count,
        )
        logger.warning(
            "The skipped XML files are found in these common folders: %s",
            ", ".join(str(path) for path in multiples),
        )
    xmls_to_push = (f for f in found_xml if f.parent not in multiples)
    push_all(xmls_to_push, client, project)


def push_all(xmls_to_push: Iterable[Path], client: CentralClient, project: str):
    """Push all supplied XML files to ODK Central."""
    bad_resources = set()
    for single_xml in xmls_to_push:
        with open(single_xml, mode="rb") as f:
            data = f.read()
        form_id = get_form_id_from_xml(data)
        if form_id and form_id not in bad_resources:
            try:
                resp = client.post_submission(project, form_id, data)
                instance_id = resp.json()["instanceId"]
                logger.info(
                    "Successfully uploaded instance %s from file %s",
                    instance_id,
                    single_xml,
                )
                push_attachments(client, project, form_id, instance_id, single_xml)
            except HTTPError as err:
                resp = err.response
                if resp.status_code == 400:
                    msg = "ODK Central count not understand the uploaded file as a submission: %s"
                    logger.warning(msg, single_xml)
                elif resp.status_code == 404:
                    msg = (
                        "The server responded with a 404, Resource Not Found for URL %s. "
                        "Skipping %s"
                    )
                    logger.warning(msg, resp.url, single_xml)
                    bad_resources.add(form_id)
                elif resp.status_code == 409:
                    msg = (
                        "No change: ODK Central already has a submission with the "
                        "same instance ID as %s"
                    )
                    logger.warning(msg, single_xml)
                else:
                    raise
        elif form_id in bad_resources:
            logger.warning(
                "Skipping XML file with bad form ID %s, file %s", form_id, single_xml
            )
        else:
            logger.warning(
                "XML file skipped since unable to determine form id: %s", single_xml
            )


def push_attachments(
    client: CentralClient, project: str, form_id: str, instance_id: str, xml_path: Path
):
    """Push attachments in the same directory as a submission."""
    for non_xml in get_non_xml_files(xml_path.parent):
        filename = non_xml.name
        with open(non_xml, mode="rb") as f:
            data = f.read()
        try:
            client.post_attachment(project, form_id, instance_id, filename, data)
            msg = "For instance ID %s, successfully uploaded attachment %s"
            logger.info(msg, instance_id, filename)
        except HTTPError:
            msg = "For instance ID %s, ODK Central did not accept attachment %s"
            logger.info(msg, instance_id, non_xml)


def get_non_xml_files(path: Path):
    """Get all non-XML files at a given path."""
    if path.is_dir():
        files = path.glob("*")
        return (f for f in files if f.is_file() and f.suffix != ".xml")
    return iter(())


# pylint: disable=unsubscriptable-object
def get_form_id_from_xml(data: bytes) -> Optional[str]:
    """Given an XForm in bytes, get the form ID."""
    try:
        root = ET.fromstring(data)
        form_id = root.attrib.get("id")
        return form_id
    except ET.ParseError:
        return None
