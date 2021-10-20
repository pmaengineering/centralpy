"""A module to download attachments for a specific instance."""
from pathlib import Path
from typing import List, Optional, Sequence

from requests.exceptions import HTTPError

from centralpy.client import CentralClient


def download_attachments_from_sequence(  # pylint: disable=too-many-arguments
    client: CentralClient,
    project: str,
    form_id: str,
    instance_id: str,
    attachments: Sequence[str],
    download_dir: Path,
) -> List[Optional[Path]]:
    """Download attachments and save to local directory."""
    saved_at: List[Optional[Path]] = []
    for filename in attachments:
        try:
            attachment = client.get_attachment(project, form_id, instance_id, filename)
            download_dir.mkdir(parents=True, exist_ok=True)
            full_path = download_dir / filename
            attachment.save(full_path)
            saved_at.append(full_path)
        except HTTPError:
            saved_at.append(None)
    return saved_at


def download_all_attachments(
    client: CentralClient,
    project: str,
    form_id: str,
    instance_id: str,
    download_dir: Path,
) -> List[Optional[Path]]:
    """Download all attachments for a given instance ID to local directory."""
    attachments: List[str] = []
    attachment_listing = client.get_attachments(project, form_id, instance_id)
    for attachment_details in attachment_listing.get_attachments():
        if attachment_details["exists"]:
            attachments.append(attachment_details["name"])
    return download_attachments_from_sequence(
        client, project, form_id, instance_id, attachments, download_dir
    )
