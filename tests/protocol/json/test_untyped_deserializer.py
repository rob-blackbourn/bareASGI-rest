"""Tests for the untyped deserializer"""

from datetime import timedelta, datetime

from stringcase import snakecase, camelcase

from bareasgi_rest.protocol.config import SerializerConfig
from bareasgi_rest.protocol.json.untyped_deserializer import deserialize

CONFIG = SerializerConfig(camelcase, snakecase)


def test_deserialize():
    """Tests for deserialize"""
    text = '{"strArg": "text", "intArg": 42, "floatArg": 3.14, "dateArg": "2019-12-31T23:59:59.00Z", "durationArg": "PT1H7M"}'
    obj = deserialize(text, CONFIG)
    assert obj == {
        'str_arg': 'text',
        'int_arg': 42,
        'float_arg': 3.14,
        'date_arg': datetime(2019, 12, 31, 23, 59, 59),
        'duration_arg': timedelta(hours=1, minutes=7)
    }
