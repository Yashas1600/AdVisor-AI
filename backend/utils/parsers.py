import re
from datetime import datetime, timezone
import dateparser


def parse_upvotes(upvote_text: str) -> int:
    """
    Convert Reddit upvote string to integer.
    Examples: "1.2k" -> 1200, "5.4m" -> 5400000, "42" -> 42
    """
    if not upvote_text:
        return 0

    # Clean the text
    upvote_text = upvote_text.strip().lower().replace(',', '')

    # Handle vote/votes text
    upvote_text = re.sub(r'\s*(vote|votes)\s*', '', upvote_text)

    # Parse multipliers
    multipliers = {
        'k': 1000,
        'm': 1000000,
        'b': 1000000000
    }

    # Check for multiplier suffix
    for suffix, multiplier in multipliers.items():
        if suffix in upvote_text:
            try:
                number = float(upvote_text.replace(suffix, '').strip())
                return int(number * multiplier)
            except ValueError:
                return 0

    # No multiplier, just parse as integer
    try:
        return int(float(upvote_text))
    except ValueError:
        return 0


def parse_timestamp(timestamp_text: str) -> str:
    """
    Convert Reddit relative timestamp to ISO 8601 format.
    Examples: "3 hours ago" -> "2024-01-01T12:00:00Z"
    """
    if not timestamp_text:
        return datetime.now(timezone.utc).isoformat()

    # Use dateparser to handle relative times
    parsed_date = dateparser.parse(
        timestamp_text,
        settings={
            'TIMEZONE': 'UTC',
            'RETURN_AS_TIMEZONE_AWARE': True,
            'PREFER_DATES_FROM': 'past'
        }
    )

    if parsed_date:
        return parsed_date.isoformat()

    # Fallback to current time if parsing fails
    return datetime.now(timezone.utc).isoformat()


def clean_text(text: str) -> str:
    """Clean and normalize text content."""
    if not text:
        return ""

    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    return text.strip()
