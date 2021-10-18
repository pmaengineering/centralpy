"""A module to download attachments for a specific instance."""
from pathlib import Path
from typing import List, Optional, Tuple

from requests.exceptions import HTTPError

from centralpy.client import CentralClient


def download_attachments_from_sequence(
    client: CentralClient,
    project: str,
    form_id: str,
    instance_id: str,
    attachments: Tuple[str],
    download_dir: Path,
):
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
