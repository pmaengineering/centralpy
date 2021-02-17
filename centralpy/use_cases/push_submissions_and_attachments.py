from collections import Counter
import logging
from pathlib import Path

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
    multiples = {k: v for k, v in path_counter if v > 1}
    if multiples:
        multiples_count = sum(multiples.values())
        logging.warning(
            "Count of XML files ignored due to being in a common folder: %d",
            multiples_count,
        )
        logging.warning(
            "Ignored XML files found in these common folders: %s",
            ", ".join(str(path) for path in multiples),
        )
    for single_xml in (f for f in found_xml if f.parent not in multiples):
        pass
