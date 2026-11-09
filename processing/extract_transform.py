import re
import logging


logger = logging.getLogger(__name__)


def extract(row):
    pattern = re.compile(
        r'(?P<month>\w{3})\s+(?P<day>\d{1,2})\s'
        r'(?P<time>\d{2}:\d{2}:\d{2})\s\S+\s\S+:\s'
        r'(?P<message>.+)'
    )

    match = pattern.search(row)

    if match:
        message = match.group("message")

        attempt_pattern = re.compile(
            r"(?P<status>Failed|Accepted) "
            r"(?P<method>password|none) for "
            r"(?P<invalid>invalid user )?"
            r"(?P<user>\S*) from "
            r"(?P<ip>\d+\.\d+\.\d+\.\d+)"
        )

        attempt_match = attempt_pattern.search(message)

        if attempt_match:
            result = match.groupdict()
            result.update(attempt_match.groupdict())

            repetition_match = re.search(
                r"message repeated (?P<count>\d+) times:",
                message
            )

            if repetition_match:
                result["count"] = int(
                    repetition_match.group("count")
                )
            else:
                result["count"] = 1

            return result

    if "Failed " in row or "Accepted " in row:
        logger.warning(
            f"Tentative non reconnue par l'extraction : {row.strip()}"
        )

    return None