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
    Tuple
)
from urllib.parse import parse_qs

from bareasgi import text_reader, text_writer
from bareasgi.basic_router.http_router import BasicHttpRouter
from baretypes import (
    RouteMatches,
    Scope,
    Info,
    Content,
    HttpResponse
)
import bareutils.header as header

from .utils import make_args, JSONEncoderEx, as_datetime

LOGGER = logging.getLogger(__name__)


def _make_writer(data: Any, accept: Mapping[bytes, Tuple[bytes, Any]]) -> Tuple[bytes, AsyncIterator[bytes]]:
    if any(key.startswith(b'application/json') or key.startswith(b'*/*') for key in accept.keys()):
        return b'application/json', text_writer(json.dumps(data, cls=JSONEncoderEx))
    elif any(key.startswith(b'text/plain') for key in accept.keys()):
        return b'text/plain', text_writer(data if isinstance(data, str) else str(data))
    raise TypeError

class RestHttpRouter(BasicHttpRouter):
    """A REST router"""

    def add_rest(
            self,
            methods: AbstractSet[str],
            path: str,
            callback: Callable[..., Awaitable[Any]]
    ) -> None:
        """Add a rest callback"""
        LOGGER.debug('Adding route for %s on "%s"', methods, path)

        for method in methods:
            self._add_method(method, path, callback)

    def _add_method(
            self,
            method: str,
            path: str,
            callback: Callable[..., Awaitable[Any]]
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

            if method in {'GET'}:
                body_args: Dict[str, Any] = {}
            else:
                media_type, params = header.content_type(scope['headers']) or b'', None
                if media_type.startswith(b'application/json'):
                    body = await text_reader(content)
                    body_args = json.loads(body, object_hook=as_datetime)
                elif media_type.startswith(b'application/x-www-form-urlencoded'):
                    body = await text_reader(content)
                    body_args = parse_qs(body)
                elif media_type.startswith(b'multipart/form-data') and params is not None:
                    body = await text_reader(content)
                    body_args = parse_multipart(io.StringIO(body), params[b"boundary"])
                else:
                    raise TypeError

            args, kwargs = make_args(sig, matches, query_args, body_args)

            response = await callback(*args, **kwargs)
            response_content_type, writer = _make_writer(response, accept)
            return 200, [(b'content-type', response_content_type)], writer

        self.add({'GET'}, path, http_request_callback)
