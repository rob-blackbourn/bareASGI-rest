"""Tests for JSON serialization"""

from bareasgi_rest.protocol.iso_8601 import (
    iso_8601_to_datetime,
    datetime_to_iso_8601
)


def test_json():
    """Test for json_to_python"""
    for text in [
            '2014-01-01T23:28:56.782Z',
            '2014-02-01T09:28:56.321-10:00',
            '2014-02-01T09:28:56.321+00:00'
    ]:
        timestamp = iso_8601_to_datetime(text)
        roundtrip = datetime_to_iso_8601(timestamp)
        assert text == roundtrip
