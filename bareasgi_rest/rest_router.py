"""A router for REST APIs

Attributes:
    DEFAULT_SWAGGER_BASE_URL (str): The default swagger CDN url. The currently
        supported version is 3.4.0
    DEFAULT_TYPEFACE_URL (str): The typeface url to use.
    DEFAULT_CONSUMES
"""

import inspect
import logging
from typing import (
    AbstractSet,
    Any,
    AsyncIterator,
    Awaitable,
    Callable,
    Dict,
    List,
    Mapping,
    Optional,
    cast
)
from urllib.error import HTTPError
from urllib.parse import parse_qs

from bareasgi import text_reader, text_writer
from bareasgi.basic_router.http_router import BasicHttpRouter, PathDefinition
from baretypes import (
    RouteMatches,
    Scope,
    Info,
    Content,
    HttpResponse
)
import bareutils.header as header
from inflection import underscore

from .protocol.json import camelcase_object
from .arg_builder import make_args
from .swagger import SwaggerRepository, SwaggerConfig, SwaggerController
from .constants import (
    DEFAULT_SWAGGER_BASE_URL,
    DEFAULT_TYPEFACE_URL,
    DEFAULT_CONSUMES,
    DEFAULT_PRODUCES,
    DEFAULT_COLLECTION_FORMAT,
    DEFAULT_NOT_FOUND_RESPONSE
)
from .types import (
    Deserializer,
    DictConsumes,
    DictProduces,
    RestCallback
)
from .utils import camelcase

LOGGER = logging.getLogger(__name__)


class RestHttpRouter(BasicHttpRouter):
    """A REST router"""

    def __init__(
            self,
            not_found_response: HttpResponse,
            *,
            title: str,
            version: str,
            description: Optional[str] = None,
            base_path: str = '',
            consumes: DictConsumes = DEFAULT_CONSUMES,
            produces: DictProduces = DEFAULT_PRODUCES,
            tags: Optional[List[Mapping[str, Any]]] = None,
            swagger_base_url: str = DEFAULT_SWAGGER_BASE_URL,
            typeface_url: str = DEFAULT_TYPEFACE_URL,
            config: Optional[SwaggerConfig] = None
    ) -> None:
        """Initialise the REST router

        Args:
            not_found_response (HttpResponse): The response sent when a route is
                not found
            title (str): The title of the swagger documentation
            version (str): The version of the exposed API
            description (Optional[str], optional): The API description. Defaults
                to None.
            base_path (str, optional): The base path of the API. Defaults to ''.
            consumes (DictConsumes, optional): A map of media types and
                deserializers. Defaults to DEFAULT_CONSUMES.
            produces (DictProduces, optional): A map of media types and
                serializers. Defaults to DEFAULT_PRODUCES.
            tags (Optional[List[Mapping[str, Any]]], optional): The available
                tags. Defaults to None.
            swagger_base_url (Optional[str], optional): The base url for the
                swagger CDN. Defaults to DEFAULT_SWAGGER_BASE_URL.
            typeface_url (Optional[str], optional): The base url for the
                typeface. Defaults to DEFAULT_TYPEFACE_URL.
            config (Optional[SwaggerConfig], optional): The swagger
                configuration. Defaults to None.
        """
        super().__init__(not_found_response or DEFAULT_NOT_FOUND_RESPONSE)
        self.consumes = consumes
        self.produces = produces
        self.base_path = base_path

        self.accepts: Dict[str, Dict[PathDefinition, bytes]] = {}
        self.collection_formats: Dict[str, Dict[PathDefinition, str]] = {}

        self.swagger_repo = SwaggerRepository(
            title,
            version,
            description,
            base_path,
            [name.decode() for name in self.consumes.keys()],
            [name.decode() for name in self.produces.keys()],
            tags
        )
        self.swagger_controller = SwaggerController(
            title,
            base_path,
            swagger_base_url,
            typeface_url,
            config,
            self.swagger_repo
        )
        self.swagger_controller.add_routes(self)

    def add_rest(
            self,
            methods: AbstractSet[str],
            path: str,
            callback: RestCallback,
            *,
            accept: bytes = b'application/json',
            content_type: bytes = b'application/json',
            collection_format: str = DEFAULT_COLLECTION_FORMAT,
            tags: Optional[List[str]] = None,
            status_code: int = 200,
            status_description: str = 'OK'
    ) -> None:
        """Register a callback to a method and path

        Args:
            methods (AbstractSet[str]): The set of methods
            path (str): The path
            callback (RestCallback): The callback
            accept (bytes, optional): The accept media type. Defaults to
                b'application/json'.
            content_type (bytes, optional): The content media type. Defaults
                to b'application/json'.
            collection_format (str, optional): The format of repeated values.
                Defaults to DEFAULT_COLLECTION_FORMAT.
            tags (Optional[List[str]], optional): A list of tags. Defaults to
                None.
            status_code (int, optional): The ok status code. Defaults to 200.
            status_description (str, optional): The ok status message. Defaults
                to 'OK'.
        """
        LOGGER.debug('Adding route for %s on "%s"', methods, path)

        for method in methods:
            self._add_method(
                method,
                path,
                callback,
                content_type,
                status_code
            )
            self.swagger_repo.add(
                method,
                path,
                callback,
                accept,
                content_type,
                collection_format,
                tags,
                status_code,
                status_description
            )

    def _add_method(
            self,
            method: str,
            path: str,
            callback: RestCallback,
            content_type: bytes,
            status_code: int
    ) -> None:
        signature = inspect.signature(callback)
        path_definition = PathDefinition(self.base_path + path)

        async def rest_callback(
                scope: Scope,
                _info: Info,
                matches: RouteMatches,
                content: Content
        ) -> HttpResponse:

            route_args: Dict[str, str] = {
                underscore(name): value
                for name, value in matches.items()
            }
            query_string = scope['query_string'].decode()
            query_args: Dict[str, List[str]] = {
                underscore(name): values
                for name, values in parse_qs(query_string).items()
            }
            body_reader = self._get_body_reader(scope, content)

            args, kwargs = await make_args(
                signature,
                route_args,
                query_args,
                body_reader,
                underscore,
                camelcase
            )

            try:
                body = await callback(*args, **kwargs)
            except HTTPError as error:
                raise HTTPError(
                    scope['path'],
                    error.code if error.code is not None else 500,
                    error.reason,
                    scope['headers'],
                    None
                )

            accept = header.accept(scope['headers'])
            writer = self._make_writer(body, accept)
            headers = [
                (b'content-type', content_type)
            ]
            return status_code, headers, writer

        self.add_route(method, path_definition, rest_callback)

    def _make_writer(
            self,
            data: Optional[Any],
            accept: Optional[Mapping[bytes, float]]
    ) -> Optional[AsyncIterator[bytes]]:
        if data is None:
            # No need for a writer if there is no data.
            return None

        if not accept:
            accept = {b'application/json': 1.0}

        for media_type in accept.keys():
            if media_type in self.produces:
                serializer = self.produces[media_type]
                break
        else:
            serializer = self.produces[b'application/json']

        text = serializer(camelcase_object(data))
        return text_writer(text)

    def _get_body_reader(
            self,
            scope: Scope,
            content: Content
    ) -> Callable[[Any], Awaitable[Any]]:
        if scope['method'] in {'GET'}:
            deserializer: Optional[Deserializer] = None
        else:
            media_type, params = header.content_type(
                scope['headers']
            ) or (b'application/json', cast(Dict[bytes, Any], {}))
            deserializer = self.consumes.get(media_type)

        async def body_reader(annotation: Any) -> Any:
            if deserializer is None:
                raise RuntimeError('No deserializer')
            text = await text_reader(content)
            return deserializer(
                text,
                media_type,
                params,
                annotation,
                underscore,
                camelcase
            )

        return body_reader
