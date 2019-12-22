"""A router for REST"""

from cgi import parse_multipart
import io
import inspect
import logging
import json
from typing import (
    AbstractSet,
    Any,
    AsyncIterator,
    Awaitable,
    Callable,
    Dict,
    Mapping,
    Optional,
    Tuple,
    cast
)
from urllib.parse import parse_qs

from bareasgi import text_reader, text_writer
from bareasgi.basic_router.http_router import BasicHttpRouter
from baretypes import (
    RouteMatches,
    Scope,
    Info,
    Content,
    HttpResponse,
    Headers
)
import bareutils.header as header
import bareasgi_jinja2

from .utils import make_args, JSONEncoderEx, camelize_object

LOGGER = logging.getLogger(__name__)

DEFAULT_SWAGGER_BASE_URL = "https://cdnjs.cloudflare.com/ajax/libs/swagger-ui/3.24.2"
DEFAULT_TYPEFACE_URL = "https://fonts.googleapis.com/css?family=Roboto:300,400,500,700&display=swap"

WriterFactory = Callable[
    [Optional[Any], Mapping[bytes, Tuple[bytes, Any]]],
    Tuple[bytes, Optional[AsyncIterator[bytes]]]
]


def _make_writer(
        data: Optional[Any],
        accept: Mapping[bytes, Tuple[bytes, Any]]
) -> Tuple[bytes, Optional[AsyncIterator[bytes]]]:
    if any(key.startswith(b'application/json') or key.startswith(b'*/*') for key in accept.keys()):
        writer = None if data is None else text_writer(
            json.dumps(
                camelize_object(data),
                cls=JSONEncoderEx
            )
        )
        return b'application/json', writer
    elif any(key.startswith(b'text/plain') for key in accept.keys()):
        writer = None if data is None else text_writer(
            data if isinstance(data, str) else str(data))
        return b'text/plain', writer
    raise TypeError


async def _get_body_args(
        method: str,
        headers: Headers,
        content: Content
) -> Dict[str, Any]:
    if method in {'GET'}:
        return {}

    media_type, params = header.content_type(
        headers) or (b'', cast(Dict[bytes, Any], {}))
    if media_type.startswith(b'application/json'):
        body = await text_reader(content)
        return json.loads(body)
    elif media_type.startswith(b'application/x-www-form-urlencoded'):
        body = await text_reader(content)
        return parse_qs(body)
    elif media_type.startswith(b'multipart/form-data') and b"boundary" in params:
        body = await text_reader(content)
        return parse_multipart(io.StringIO(body), params[b"boundary"])
    else:
        raise TypeError


class RestHttpRouter(BasicHttpRouter):
    """A REST router"""

    def __init__(
        self,
        not_found_response: HttpResponse,
        *,
        title: str = 'REST API',
        writer_factory: Optional[WriterFactory] = None,
        swagger_base_url: Optional[str] = None,
        typeface_url: Optional[str] = None
    ) -> None:
        super().__init__(not_found_response)
        self._writer_factory = writer_factory or _make_writer
        self.title = title
        self.swagger_base_url = swagger_base_url or DEFAULT_SWAGGER_BASE_URL
        self.typeface_url = typeface_url or DEFAULT_TYPEFACE_URL

    def add_rest(
            self,
            methods: AbstractSet[str],
            path: str,
            callback: Callable[..., Awaitable[Tuple[int, Any]]],
            *,
            writer_factory: Optional[WriterFactory] = None
    ) -> None:
        """Add a rest callback"""
        LOGGER.debug('Adding route for %s on "%s"', methods, path)

        for method in methods:
            self._add_method(
                method,
                path,
                writer_factory or self._writer_factory,
                callback
            )

    def _add_method(
            self,
            method: str,
            path: str,
            writer_factory: WriterFactory,
            callback: Callable[..., Awaitable[Tuple[int, Any]]]
    ) -> None:
        sig = inspect.signature(callback)

        async def http_request_callback(
                scope: Scope,
                _info: Info,
                matches: RouteMatches,
                content: Content
        ) -> HttpResponse:
            accept = header.accept(scope['headers'])

            query_args = parse_qs(scope['query_string'].decode())
            body_args = await _get_body_args(method, scope['headers'], content)

            args, kwargs = make_args(sig, matches, query_args, body_args)

            status_code, response = await callback(*args, **kwargs)
            response_content_type, writer = writer_factory(response, accept)
            headers = [
                (b'content-type', response_content_type)
            ]
            return status_code, headers, writer

        self.add({method}, path, http_request_callback)

    async def swagger_json(
            self,
            _scope: Scope,
            _info: Info,
            _matches: RouteMatches,
            _content: Content
    ) -> HttpResponse:
        spec = """
{
  "swagger": "2.0",
  "info": {
    "title": "Sample API",
    "description": "API description in Markdown.",
    "version": "1.0.0"
  },
  "host": "api.example.com",
  "basePath": "/v1",
  "schemes": [
      "http",
      "https"
  ],
  "paths": {
    "/users": {
      "get": {
        "summary": "Returns a list of users.",
        "description": "Optional extended description in Markdown.",
        "produces": [
          "application/json"
        ],
        "responses": {
          "200": {
            "description": "OK"
          }
        }
      }
    }
  }
}
"""
        return 200, [(b'content-type', b'application/json')], text_writer(spec)

    @bareasgi_jinja2.template('swagger.html')
    async def swagger_ui(
            self,
            _scope: Scope,
            _info: Info,
            _matches: RouteMatches,
            _content: Content
    ) -> Dict[str, Any]:
        """The swagger view"""
        return {
            "title": self.title,
            "specs_url": "/api/1/swagger.json",
            'swagger_base_url': self.swagger_base_url,
            "swagger_oauth_client_id": False,
            "swagger_oauth_realm": None,
            "swagger_oauth_app_name": None,
            "swagger_oauth2_redirect_url": None,
            "swagger_validator_url": None,
            "swagger_supported_submit_methods": None,
            "swagger_operation_id": None,
            "swagger_request_duration": None,
            "swagger_doc_expansion": None,
            'typeface_url': self.typeface_url,
        }
