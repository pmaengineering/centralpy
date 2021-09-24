from io import BufferedReader
import logging
from pathlib import Path
from typing import Tuple

from requests.exceptions import HTTPError

from centralpy.client import CentralClient


logger = logging.getLogger(__name__)


def update_attachments_from_sequence(
    client: CentralClient,
    project: int,
    form_id: str,
    instance_id: str,
    attachments: Tuple[BufferedReader],
):
    """Upload attachments to ODK Central."""
    for item in attachments:
        relative_path = Path(item.name)
        filename = relative_path.name
        data = item.read()
        try:
            client.post_attachment(project, form_id, instance_id, filename, data)
            logger.info('Successfully uploaded data for attachment "%s"', filename)
        except HTTPError as err:
            response = err.response
            if response.status_code == 404:
                attachments = client.get_attachments(project, form_id, instance_id)
                logger.warning(
                    'Unable to upload to "%s" for instance ID "%s" '
                    "because it is not an expected attachment",
                    filename,
                    instance_id,
                )
            else:
                raise
