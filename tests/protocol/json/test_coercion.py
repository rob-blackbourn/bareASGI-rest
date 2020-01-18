"""Tests for JSON serialization"""

from bareasgi_rest.protocol.json.coercion import (
    camelize_object,
    underscore_object,
)


def test_casing():
    """Tests for camelize and underscore"""
    orig_dct = {
        'first_name': 'rob',
        'addresses': [
            {
                'street_name': 'my street'
            },
            {
                'street_name': 'my other street'
            }
        ]
    }
    camel_dct = camelize_object(orig_dct)
    assert camel_dct == {
        'firstName': 'rob',
        'addresses': [
            {
                'streetName': 'my street'
            },
            {
                'streetName': 'my other street'
            }
        ]
    }
    underscore_dct = underscore_object(camel_dct)
    assert underscore_dct == orig_dct
