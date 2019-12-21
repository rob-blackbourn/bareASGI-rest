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

from .utils import make_args, JSONEncoderEx, camelize_object

LOGGER = logging.getLogger(__name__)

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
        writer_factory: Optional[WriterFactory] = None
    ) -> None:
        super().__init__(not_found_response)
        self._writer_factory = writer_factory or _make_writer

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
