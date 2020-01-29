"""Constants"""

from baretypes import HttpResponse
from bareutils import text_writer
from stringcase import camelcase, snakecase, pascalcase

from jetblack_serialization.config import SerializerConfig

from .types import (
    DictConsumes,
    DictProduces,
    DictSerializerConfig
)

from .serialization.json import (
    to_json,
    from_json,
    from_form_data,
    from_query_string,
    json_arg_deserializer_factory
)
from .serialization.xml import (
    from_xml,
    to_xml
)
from .swagger import SwaggerConfig

DEFAULT_SWAGGER_BASE_URL = "https://cdnjs.cloudflare.com/ajax/libs/swagger-ui/3.4.0"
DEFAULT_TYPEFACE_URL = "https://fonts.googleapis.com/css?family=Roboto:300,400,500,700&display=swap"

DEFAULT_CONSUMES: DictConsumes = {
    b'application/json': from_json,
    b'*/*': from_json,
    b'application/x-www-form-urlencoded': from_query_string,
    b'multipart/form-data': from_form_data,
    b'application/xml': from_xml,
}

DEFAULT_PRODUCES: DictProduces = {
    b'application/json': to_json,
    b'*/*': to_json,
    b'application/xml': to_xml,
}

DEFAULT_COLLECTION_FORMAT = 'multi'

DEFAULT_NOT_FOUND_RESPONSE: HttpResponse = (
    404,
    [(b'content-type', b'text/plain')],
    text_writer('Not Found'),
    None
)

DEFAULT_JSON_SERIALIZER_CONFIG = SerializerConfig(camelcase, snakecase)
DEFAULT_XML_SERIALIZER_CONFIG = SerializerConfig(pascalcase, snakecase)

DEFAULT_SERIALIZER_CONFIG: DictSerializerConfig = {
    b'application/json': DEFAULT_JSON_SERIALIZER_CONFIG,
    b'application/xml': DEFAULT_XML_SERIALIZER_CONFIG,
}

DEFAULT_ARG_DESERIALIZER_FACTORY = json_arg_deserializer_factory

DEFAULT_SWAGGER_CONFIG = SwaggerConfig(
    serialize_key=camelcase,
    deserialize_key=snakecase
)
