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
    AsyncIterable,
    Awaitable,
    Callable,
    Mapping,
    Sequence,
    cast
)
from urllib.parse import parse_qs

from bareasgi import HttpRequest, HttpResponse, text_reader, text_writer
from bareasgi.basic_router.http_router import BasicHttpRouter, PathDefinition
from bareutils import header, response_code
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
    ArgDeserializerFactory,
    RestError,
    Serializer
)

LOGGER = logging.getLogger(__name__)


def _rename_path_definition(
        path_definition: PathDefinition,
        config: SerializerConfig
) -> PathDefinition:
    for segment in path_definition.segments:
        if segment.is_variable:
            segment.name = config.serialize_key(segment.name)
    return path_definition


def _is_simple_callback(signature: inspect.Signature) -> bool:
    return (
        len(signature.parameters) == 1 and
        next(iter(signature.parameters.values())).annotation is HttpRequest and
        signature.return_annotation is HttpResponse
    )


class RestHttpRouter(BasicHttpRouter):
    """A REST router"""

    def __init__(
            self,
            title: str = "bareASGI Rest API",
            version: str = "1",
            *,
            not_found_response: HttpResponse | None = None,
            description: str | None = None,
            base_path: str = '',
            consumes: DictConsumes | None = None,
            produces: DictProduces | None = None,
            tags: list[Mapping[str, Any]] | None = None,
            swagger_base_url: str = DEFAULT_SWAGGER_BASE_URL,
            typeface_url: str = DEFAULT_TYPEFACE_URL,
            config: SwaggerConfig = DEFAULT_SWAGGER_CONFIG,
            serializer_configs: DictSerializerConfig | None = None,
            arg_serializer_config: SerializerConfig = DEFAULT_JSON_SERIALIZER_CONFIG,
            arg_deserializer_factory: ArgDeserializerFactory = DEFAULT_ARG_DESERIALIZER_FACTORY
    ) -> None:
        """Initialise the REST router

        Here is an example of how to use the router.

        ```python
        from bareasgi import Application
        from bareasgi_rest import RestHttpRouter, add_swagger_ui

        router = RestHttpRouter(
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
            title (str): The title of the swagger documentation.
            version (str): The version of the exposed API.
            not_found_response (HttpResponse | None, optional): The response
                sent when a route is not found. Defaults to None.
            description (str | None, optional): The API description. Defaults
                to None.
            base_path (str, optional): The base path of the API. Defaults to ''.
            consumes (DictConsumes | None, optional): A map of media types
                and deserializers. Defaults to DEFAULT_CONSUMES.
            produces (DictProduces | None, optional): A map of media types
                and serializers. Defaults to DEFAULT_PRODUCES.
            tags (list[Mapping[str, Any]] | None, optional): The available
                tags. Defaults to None.
            swagger_base_url (str | None, optional): The base url for the
                swagger CDN. Defaults to DEFAULT_SWAGGER_BASE_URL.
            typeface_url (str | None, optional): The base url for the
                typeface. Defaults to DEFAULT_TYPEFACE_URL.
            config (SwaggerConfig | None, optional): The swagger
                configuration. Defaults to None.
            serializer_configs (DictSerializerConfig | None, optional): The
                serializer configuration for content. Defaults to
                DEFAULT_SERIALIZER_CONFIG.
            arg_serializer_config (BaseSerializerConfig, optional): The serializer
                configuration for arguments. Defaults to DEFAULT_JSON_SERIALIZER_CONFIG.
            arg_deserializer_factory (ArgDeserializerFactory, optional): The
                deserializer configuration for arguments. Defaults to
                DEFAULT_ARG_DESERIALIZER_FACTORY.
        """
        super().__init__(not_found_response or DEFAULT_NOT_FOUND_RESPONSE)
        self.consumes = consumes or DEFAULT_CONSUMES
        self.produces = produces or DEFAULT_PRODUCES
        self.base_path = base_path

        self.accepts: dict[str, dict[PathDefinition, bytes]] = {}
        self.collection_formats: dict[str, dict[PathDefinition, str]] = {}

        self.serializer_configs = serializer_configs or DEFAULT_SERIALIZER_CONFIG
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
            methods: set[str],
            path: str,
            callback: RestCallback,
            *,
            consumes: Sequence[bytes] | None = None,
            produces: Sequence[bytes] | None = None,
            collection_format: str = DEFAULT_COLLECTION_FORMAT,
            tags: list[str] | None = None,
            status_code: int = response_code.OK,
            status_description: str = 'OK',
            serializer_config: DictSerializerConfig | None = None,
            arg_serializer_config: SerializerConfig | None = None,
            arg_deserializer_factory: ArgDeserializerFactory | None = None
    ) -> None:
        """Register a callback to a method and path

        Args:
            methods (set[str]): The set of methods
            path (str): The path
            callback (RestCallback): The callback
            produces (List[bytes], optional): The accept media type. Defaults to
                None.
            consumes (List[bytes], optional): The content media type. Defaults
                to None.
            collection_format (str, optional): The format of repeated values.
                Defaults to DEFAULT_COLLECTION_FORMAT.
            tags (list[str] | None, optional): A list of tags. Defaults to
                None.
            status_code (int, optional): The ok status code. Defaults to 200.
            status_description (str, optional): The ok status message. Defaults
                to 'OK'.
            serializer_config (DictSerializerConfig | None, optional): The
                serializer configuration for content. Defaults to None.
            arg_serializer_config (BaseSerializerConfig | None, optional): The
                serializer configuration for arguments. Defaults to None.
            arg_deserializer_factory (ArgDeserializerFactory | None, optional): The
                deserializer configuration for arguments. Defaults to None.
        """
        LOGGER.debug('Adding route for %s on "%s"', methods, path)

        signature = inspect.signature(callback)
        if _is_simple_callback(signature):
            self.add(
                methods,
                path,
                callback
            )
            return

        if produces is None:
            produces = list(self.produces.keys())
        if consumes is None:
            consumes = list(self.consumes.keys())

        path_definition = _rename_path_definition(
            PathDefinition(self.base_path + path),
            DEFAULT_JSON_SERIALIZER_CONFIG
        )

        for method in methods:
            self._add_method(
                method,
                path_definition,
                signature,
                callback,
                consumes,
                produces,
                collection_format,
                tags,
                status_code,
                status_description,
                serializer_config,
                arg_serializer_config,
                arg_deserializer_factory
            )

    def _add_method(
            self,
            method: str,
            path_definition: PathDefinition,
            signature: inspect.Signature,
            callback: RestCallback,
            consumes: Sequence[bytes],
            produces: Sequence[bytes],
            collection_format: str,
            tags: list[str] | None,
            status_code: int,
            status_description: str,
            serializer_configs: DictSerializerConfig | None,
            arg_serializer_config: SerializerConfig | None,
            arg_deserializer_factory: ArgDeserializerFactory | None
    ) -> None:
        self.swagger_repo.add(
            method,
            path_definition,
            callback,
            consumes,
            produces,
            collection_format,
            tags,
            status_code,
            status_description
        )

        arg_deserializer = (
            arg_deserializer_factory or self.arg_deserializer_factory
        )(
            arg_serializer_config or self.arg_serializer_config
        )

        async def rest_callback(request: HttpRequest) -> HttpResponse:

            route_args: dict[str, str] = {
                self.arg_serializer_config.deserialize_key(name): value
                for name, value in request.matches.items()
            }
            query_string = request.scope['query_string'].decode()
            query_args: dict[str, list[str]] = {
                self.arg_serializer_config.deserialize_key(name): values
                for name, values in parse_qs(query_string).items()
            }
            body_reader = self._get_body_reader(request)

            try:
                args, kwargs = await make_args(
                    signature,
                    route_args,
                    query_args,
                    body_reader,
                    arg_deserializer
                )
            except BaseException as error:  # pylint: disable=broad-except
                return HttpResponse.from_text(
                    "Failed to make args:" + ". ".join(error.args),
                    status=response_code.BAD_REQUEST
                )

            try:
                body = await callback(*args, **kwargs)
            except RestError as error:
                return HttpResponse.from_text(
                    error.message,
                    status=error.status
                )
            except BaseException as error:  # pylint: disable=broad-except
                return HttpResponse.from_text(
                    str(error),
                    status=response_code.INTERNAL_SERVER_ERROR
                )

            accept = header.accept(request.scope['headers'])
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
                    if b'*/*' in accept:
                        # Prefer the first content type that is supported.
                        content_type = produces[0]
                    else:
                        return HttpResponse.from_text(
                            'Unsupported media type',
                            status=response_code.UNSUPPORTED_MEDIA_TYPE
                        )

            headers = [
                (b'content-type', content_type)
            ]

            return HttpResponse(status_code, headers, writer)

        self.add_route(method, path_definition, rest_callback)

    def _make_writer(
            self,
            data: Any | None,
            accept: Mapping[bytes, Mapping[bytes, Any]] | None,
            return_annotation: Any,
            serializer_configs: DictSerializerConfig
    ) -> AsyncIterable[bytes] | None:
        if data is None:
            # No need for a writer if there is no data.
            return None

        # Prefer the media types in the order they are defined.
        media_type: bytes | None = None
        serializer: Serializer | None = None
        if accept:
            for media_type, serializer in self.produces.items():
                if media_type in accept:
                    break
        else:
            # If no accept choose the first from produces.
            media_type, serializer = next(iter(self.produces.items()))

        if media_type is None or serializer is None:
            raise ValueError(
                f'No handler for media types: {(accept or {}).keys()}'
            )

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
            request: HttpRequest
    ) -> Callable[[Any], Awaitable[Any]]:
        if request.scope['method'] in {'GET'}:
            media_type = b'application/json'
            params: Mapping[bytes, Any] | None = {}
            deserializer: Deserializer | None = None
            serializer_config: SerializerConfig = DEFAULT_JSON_SERIALIZER_CONFIG
        else:
            media_type, params = header.content_type(
                request.scope['headers']
            ) or (b'application/json', cast(dict[bytes, Any], {}))
            deserializer = self.consumes[media_type]
            serializer_config = self.serializer_configs[media_type]

        async def body_reader(annotation: Any) -> Any:
            if deserializer is None:
                raise RuntimeError('No deserializer')
            text = await text_reader(request.body)
            return deserializer(
                media_type,
                cast(dict[bytes, Any], params),
                serializer_config,
                text,
                annotation
            )

        return body_reader
