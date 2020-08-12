"""A router for REST APIs

Attributes:
    DEFAULT_SWAGGER_BASE_URL (str): The default swagger CDN url. The currently
        supported version is 3.4.0
    DEFAULT_TYPEFACE_URL (str): The typeface url to use.
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
import bareutils.response_code as response_code
from jetblack_serialization.config import SerializerConfig

from .arg_builder import make_args
from .swagger import SwaggerRepository, SwaggerConfig, SwaggerController
from .constants import (
    DEFAULT_SWAGGER_BASE_URL,
    DEFAULT_TYPEFACE_URL,
    DEFAULT_CONSUMES,
    DEFAULT_PRODUCES,
    DEFAULT_COLLECTION_FORMAT,
    DEFAULT_NOT_FOUND_RESPONSE,
    DEFAULT_SERIALIZER_CONFIG,
    DEFAULT_JSON_SERIALIZER_CONFIG,
    DEFAULT_ARG_DESERIALIZER_FACTORY,
    DEFAULT_SWAGGER_CONFIG
)
from .types import (
    Deserializer,
    DictConsumes,
    DictProduces,
    DictSerializerConfig,
    RestCallback,
    ArgDeserializerFactory
)

LOGGER = logging.getLogger(__name__)


def _rename_path_definition(
        path_definition: PathDefinition,
        config: SerializerConfig
) -> PathDefinition:
    for segment in path_definition.segments:
        if segment.is_variable:
            segment.name = config.serialize_key(
                segment.name
            ) if config.serialize_key else segment.name
    return path_definition


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
            config: SwaggerConfig = DEFAULT_SWAGGER_CONFIG,
            serializer_configs: DictSerializerConfig = DEFAULT_SERIALIZER_CONFIG,
            arg_serializer_config: SerializerConfig = DEFAULT_JSON_SERIALIZER_CONFIG,
            arg_deserializer_factory: ArgDeserializerFactory = DEFAULT_ARG_DESERIALIZER_FACTORY
    ) -> None:
        """Initialise the REST router

        Here is an example of how to use the router.

        ```python
        from bareasgi import Application
        from bareasgi_rest import RestHttpRouter, add_swagger_ui


        router = RestHttpRouter(
            None,
            title="Books",
            version="1",
            description="A book api",
            base_path='/api/1',
            tags=[
                {
                    'name': 'Books',
                    'description': 'The book store API'
                }
            ]
        )
        app = Application(http_router=router)
        add_swagger_ui(app)
        ```        

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
            serializer_configs (DictSerializerConfig, optional): The serializer
                configuration for content. Defaults to DEFAULT_SERIALIZER_CONFIG.
            arg_serializer_config (SerializerConfig, optional): The serializer
                configuration for arguments. Defaults to DEFAULT_JSON_SERIALIZER_CONFIG.
            arg_deserializer_factory (ArgDeserializerFactory, optional): The
                deserializer configuration for arguments. Defaults to
                DEFAULT_ARG_DESERIALIZER_FACTORY.
        """
        super().__init__(not_found_response or DEFAULT_NOT_FOUND_RESPONSE)
        self.consumes = consumes
        self.produces = produces
        self.base_path = base_path

        self.accepts: Dict[str, Dict[PathDefinition, bytes]] = {}
        self.collection_formats: Dict[str, Dict[PathDefinition, str]] = {}

        self.serializer_configs = serializer_configs
        self.arg_serializer_config = arg_serializer_config
        self.arg_deserializer_factory = arg_deserializer_factory

        self.swagger_repo = SwaggerRepository(
            title,
            version,
            description,
            base_path,
            [name.decode() for name in self.consumes.keys()],
            [name.decode() for name in self.produces.keys()],
            tags,
            config
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
            consumes: List[bytes] = [b'application/json'],
            produces: List[bytes] = [b'application/json'],
            collection_format: str = DEFAULT_COLLECTION_FORMAT,
            tags: Optional[List[str]] = None,
            status_code: int = response_code.OK,
            status_description: str = 'OK',
            serializer_config: Optional[DictSerializerConfig] = None,
            arg_serializer_config: Optional[SerializerConfig] = None,
            arg_deserializer_factory: Optional[ArgDeserializerFactory] = None
    ) -> None:
        """Register a callback to a method and path

        Args:
            methods (AbstractSet[str]): The set of methods
            path (str): The path
            callback (RestCallback): The callback
            produces (List[bytes], optional): The accept media type. Defaults to
                b'application/json'.
            consumes (List[bytes], optional): The content media type. Defaults
                to b'application/json'.
            collection_format (str, optional): The format of repeated values.
                Defaults to DEFAULT_COLLECTION_FORMAT.
            tags (Optional[List[str]], optional): A list of tags. Defaults to
                None.
            status_code (int, optional): The ok status code. Defaults to 200.
            status_description (str, optional): The ok status message. Defaults
                to 'OK'.
            serializer_config (Optional[DictSerializerConfig], optional): The
                serializer configuration for content. Defaults to None.
            arg_serializer_config (Optional[SerializerConfig], optional): The
                serializer configuration for arguments. Defaults to None.
            arg_deserializer_factory (Optional[ArgDeserializerFactory], optional): The
                deserializer configuration for arguments. Defaults to None.
        """
        LOGGER.debug('Adding route for %s on "%s"', methods, path)

        for method in methods:
            self._add_method(
                method,
                path,
                callback,
                produces,
                status_code,
                serializer_config,
                arg_serializer_config,
                arg_deserializer_factory
            )
            self.swagger_repo.add(
                method,
                _rename_path_definition(
                    PathDefinition(path),
                    DEFAULT_JSON_SERIALIZER_CONFIG
                ),
                callback,
                consumes,
                produces,
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
            produces: List[bytes],
            status_code: int,
            serializer_configs: Optional[DictSerializerConfig],
            arg_serializer_config: Optional[SerializerConfig],
            arg_deserializer_factory: Optional[ArgDeserializerFactory]
    ) -> None:
        signature = inspect.signature(callback)
        path_definition = _rename_path_definition(
            PathDefinition(self.base_path + path),
            DEFAULT_JSON_SERIALIZER_CONFIG
        )

        arg_deserializer = (
            arg_deserializer_factory or self.arg_deserializer_factory
        )(
            arg_serializer_config or self.arg_serializer_config
        )

        async def rest_callback(
                scope: Scope,
                _info: Info,
                matches: RouteMatches,
                content: Content
        ) -> HttpResponse:

            route_args: Dict[str, str] = {
                self.arg_serializer_config.deserialize_key(name): value
                for name, value in matches.items()
            }
            query_string = scope['query_string'].decode()
            query_args: Dict[str, List[str]] = {
                self.arg_serializer_config.deserialize_key(name): values
                for name, values in parse_qs(query_string).items()
            }
            body_reader = self._get_body_reader(scope, content)

            try:
                args, kwargs = await make_args(
                    signature,
                    route_args,
                    query_args,
                    body_reader,
                    arg_deserializer
                )
            except BaseException as error:
                raise HTTPError(
                    scope['path'],
                    response_code.BAD_REQUEST,
                    ". ".join(error.args),
                    scope['headers'],
                    None  # type: ignore
                )
            try:
                body = await callback(*args, **kwargs)
            except HTTPError as error:
                raise HTTPError(
                    scope['path'],
                    error.code if error.code is not None else response_code.INTERNAL_SERVER_ERROR,
                    str(error.reason),
                    scope['headers'],
                    None  # type: ignore
                )

            accept = header.accept(scope['headers'])
            writer = self._make_writer(
                body,
                accept,
                signature.return_annotation,
                serializer_configs or self.serializer_configs
            )
            if not accept:
                content_type = produces[0]
            else:
                for content_type in produces:
                    if content_type in accept:
                        break
                else:
                    raise HTTPError(
                        scope['path'],
                        response_code.INTERNAL_SERVER_ERROR,
                        'Unhandled content type',
                        scope['headers'],
                        None  # type: ignore
                    )
            headers = [
                (b'content-type', content_type)
            ]
            return status_code, headers, writer

        self.add_route(method, path_definition, rest_callback)

    def _make_writer(
            self,
            data: Optional[Any],
            accept: Optional[Mapping[bytes, float]],
            return_annotation: Any,
            serializer_configs: DictSerializerConfig
    ) -> Optional[AsyncIterator[bytes]]:
        if data is None:
            # No need for a writer if there is no data.
            return None

        if not accept:
            accept = {b'application/json': 1.0}

        for media_type in accept.keys():
            if media_type in self.produces:
                break
        else:
            media_type = b'application/json'

        serializer = self.produces[media_type]
        serializer_config = serializer_configs[media_type]

        text = serializer(
            media_type,
            {},
            serializer_config,
            data,
            return_annotation
        )
        return text_writer(text)

    def _get_body_reader(
            self,
            scope: Scope,
            content: Content
    ) -> Callable[[Any], Awaitable[Any]]:
        if scope['method'] in {'GET'}:
            deserializer: Optional[Deserializer] = None
            serializer_config: SerializerConfig = DEFAULT_JSON_SERIALIZER_CONFIG
        else:
            media_type, params = header.content_type(
                scope['headers']
            ) or (b'application/json', cast(Dict[bytes, Any], {}))
            deserializer = self.consumes[media_type]
            serializer_config = self.serializer_configs[media_type]

        async def body_reader(annotation: Any) -> Any:
            if deserializer is None:
                raise RuntimeError('No deserializer')
            text = await text_reader(content)
            return deserializer(
                media_type,
                params,
                serializer_config,
                text,
                annotation
            )

        return body_reader
