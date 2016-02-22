from datetime import datetime
import pytz


def filter_empty_values(mapping_object: dict) -> dict:
    """Remove entries in the dict object where the value is `None`.

    >>> foobar = {'username': 'rafaelcaricio', 'team': None}
    >>> filter_empty_values(foobar)
    {'username': 'rafaelcaricio'}

    :param mapping_object: Dict object to be filtered
    """
    return {key: val for key, val in mapping_object.items() if val is not None}


def now() -> datetime:
    """
    Returns the current datetime with the correct timezone information

    >>> isinstance(now(), datetime)
    True
    """
    return datetime.utcnow().replace(tzinfo=pytz.utc)
