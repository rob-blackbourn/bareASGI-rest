"""Tests for JSON serialization"""

from datetime import datetime, timedelta
import json

from bareasgi_rest.protocol.json.serialization import (
    JSONEncoderEx,
    json_to_python
)


def test_json():
    """Test for json_to_python"""
    orig = {
        'one': 1,
        'timestamp': datetime(1967, 8, 12, 15, 42, 12),
        'nested': {
            'timestamp': datetime(1967, 8, 12, 15, 42, 12)
        },
        'duration': timedelta(minutes=12)
    }
    text = json.dumps(orig, cls=JSONEncoderEx)
    roundtrip = json.loads(text, object_hook=json_to_python)
    assert orig == roundtrip
