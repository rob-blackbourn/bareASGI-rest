"""Tests for JSON serialization"""

from datetime import datetime
import json

from bareasgi_rest.protocol.json.serialization import (
    json_to_datetime,
    datetime_to_json,
    JSONEncoderEx,
    as_datetime
)


def test_json():
    """Test for as_datetime"""
    for text in [
            '2014-01-01T23:28:56.782Z',
            '2014-02-01T09:28:56.321-10:00',
            '2014-02-01T09:28:56.321+00:00'
    ]:
        timestamp = json_to_datetime(text)
        roundtrip = datetime_to_json(timestamp)
        assert text == roundtrip

    orig = {
        'one': 1,
        'timestamp': datetime(1967, 8, 12, 15, 42, 12),
        'nested': {
            'timestamp': datetime(1967, 8, 12, 15, 42, 12)
        }
    }
    text = json.dumps(orig, cls=JSONEncoderEx)
    roundtrip = json.loads(text, object_hook=as_datetime)
    assert orig == roundtrip
