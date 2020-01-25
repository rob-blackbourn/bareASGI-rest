"""An untyped serializer"""

from datetime import datetime, timedelta
import json
from typing import Any

from stringcase import camelcase

from ..iso_8601 import datetime_to_iso_8601, timedelta_to_iso_8601


def _camelcase_if_string(key: Any) -> Any:
    return camelcase(key) if isinstance(key, str) else key


def _from_value(value: Any) -> Any:
    if isinstance(value, timedelta):
        return timedelta_to_iso_8601(value)
    elif isinstance(value, datetime):
        return datetime_to_iso_8601(value)
    else:
        return value


def _from_list(lst: list) -> list:
    return [
        _from_obj(item)
        for item in lst
    ]


def _from_dict(dct: dict) -> dict:
    return {
        _camelcase_if_string(key): _from_obj(value)
        for key, value in dct.items()
    }


def _from_obj(obj: Any) -> Any:
    if isinstance(obj, dict):
        return _from_dict(obj)
    elif isinstance(obj, list):
        return _from_list(obj)
    else:
        return _from_value(obj)


def serialize(obj: Any) -> str:
    json_obj = _from_obj(obj)
    return json.dumps(json_obj)
