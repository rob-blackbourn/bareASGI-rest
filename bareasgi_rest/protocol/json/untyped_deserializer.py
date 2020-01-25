"""An untyped deserializer"""

import json
from typing import Any

from stringcase import snakecase

from ..iso_8601 import iso_8601_to_timedelta, iso_8601_to_datetime


def _snakecase_if_str(key: Any) -> Any:
    return snakecase(key) if isinstance(key, str) else key


def _from_value(value: Any):
    if isinstance(value, str):
        try:
            return iso_8601_to_datetime(value)
        except:
            pass
        try:
            return iso_8601_to_timedelta(value)
        except:
            pass
    return value


def _from_list(lst: list) -> list:
    return [
        _from_obj(item)
        for item in lst
    ]


def _from_dict(dct: dict) -> dict:
    return {
        _snakecase_if_str(key): _from_obj(value)
        for key, value in dct.items()
    }


def _from_obj(obj: Any) -> Any:
    if isinstance(obj, dict):
        return _from_dict(obj)
    elif isinstance(obj, list):
        return _from_list(obj)
    else:
        return _from_value(obj)


def deserialize(text: str) -> Any:
    """Deserialize JSON without type information

    Args:
        text (str): The JSON string

    Returns:
        Any: The deserialised JSON object
    """
    return json.loads(text, object_hook=_from_dict)
