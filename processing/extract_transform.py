import re

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
            r"(?P<status>Failed|Accepted) password for "
            r"(?P<invalid>invalid user )?"
            r"(?P<user>\S+) from (?P<ip>\d+\.\d+\.\d+\.\d+)"
        )

        attempt_match = attempt_pattern.search(message)

        if attempt_match:
            result = match.groupdict()
            result.update(attempt_match.groupdict())
            return result