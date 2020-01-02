"""Tests for serialization"""

from datetime import datetime
import json

from bareasgi_rest.serialization import JSONEncoderEx, as_datetime

def test_as_datetime():
    """Test for as_datetime"""
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
