"""Constants"""

from baretypes import HttpResponse
from bareutils import text_writer

from .types import (
    DictConsumes,
    DictProduces
)

from .protocol.json import (
    to_json,
    from_json,
    from_form_data,
    from_query_string,
    json_arg_deserializer_factory
)

DEFAULT_SWAGGER_BASE_URL = "https://cdnjs.cloudflare.com/ajax/libs/swagger-ui/3.4.0"
DEFAULT_TYPEFACE_URL = "https://fonts.googleapis.com/css?family=Roboto:300,400,500,700&display=swap"

DEFAULT_CONSUMES: DictConsumes = {
    b'application/json': from_json,
    b'*/*': from_json,
    b'application/x-www-form-urlencoded': from_query_string,
    b'multipart/form-data': from_form_data
}

DEFAULT_PRODUCES: DictProduces = {
    b'application/json': to_json,
    b'*/*': to_json
}

DEFAULT_COLLECTION_FORMAT = 'multi'

DEFAULT_NOT_FOUND_RESPONSE: HttpResponse = (
    404,
    [(b'content-type', b'text/plain')],
    text_writer('Not Found'),
    None
)

DEFAULT_ARG_DESERIALIZER_FACTORY = json_arg_deserializer_factory
