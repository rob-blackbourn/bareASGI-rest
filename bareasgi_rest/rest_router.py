"""A router for REST APIs

Attributes:
    DEFAULT_SWAGGER_BASE_URL (str): The default swagger CDN url. The currently
        supported version is 3.4.0
    DEFAULT_TYPEFACE_URL (str): The typeface url to use.
    DEFAULT_CONSUMES
"""

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
    List,
    Mapping,
    Optional,
    cast
)
from urllib.parse import parse_qs

from bareasgi import text_reader, text_writer
from bareasgi.basic_router.http_router import BasicHttpRouter, PathDefinition
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
import docstring_parser

from .utils import make_args, JSONEncoderEx, as_datetime, camelize_object
from .swagger import (
    make_swagger_path,
    make_swagger_parameters,
    gather_error_responses,
    make_swagger_response_schema
)
from .config import SwaggerConfig

LOGGER = logging.getLogger(__name__)

DEFAULT_SWAGGER_BASE_URL = "https://cdnjs.cloudflare.com/ajax/libs/swagger-ui/3.4.0"
DEFAULT_TYPEFACE_URL = "https://fonts.googleapis.com/css?family=Roboto:300,400,500,700&display=swap"

APPLICATION_JSON = b'application/json'


def _to_json(obj: Any) -> str:
    return json.dumps(obj, cls=JSONEncoderEx)


def _from_json(text: str, _media_type: bytes, _params: Dict[bytes, bytes]) -> Any:
    return json.loads(text, object_hook=as_datetime)


def _from_query_string(text: str, _media_type: bytes, _params: Dict[bytes, bytes]) -> Any:
    return parse_qs(text)


def _from_form_data(text: str, _media_type: bytes, params: Dict[bytes, bytes]) -> Any:
    if b'boundary' not in params:
        raise RuntimeError('Required "boundary" parameter missing')
    pdict = {
        name.decode(): value
        for name, value in params.items()
    }
    return parse_multipart(io.StringIO(text), pdict)


Deserializer = Callable[[str, bytes, Dict[bytes, bytes]], Any]
DictConsumes = Dict[bytes, Deserializer]
DEFAULT_CONSUMES: DictConsumes = {
    b'application/json': _from_json,
    b'*/*': _from_json,
    b'application/x-www-form-urlencoded': _from_query_string,
    b'multipart/form-data': _from_form_data
}

Serializer = Callable[[Any], str]
DictProduces = Dict[bytes, Serializer]
DEFAULT_PRODUCES: DictProduces = {
    b'application/json': _to_json,
    b'*/*': _to_json
}

RestCallback = Callable[..., Awaitable[Any]]

DEFAULT_COLLECTION_FORMAT = 'multi'
DEFAULT_RESPONSES = {
    200: {
        'description': 'OK'
    }
}

DEFAULT_NOT_FOUND_RESPONSE: HttpResponse = (
    404,
    [(b'content-type', b'text/plain')],
    text_writer('Not Found'),
    None
)


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
        self.title = title
        self.version = version
        self.description = description
        self.consumes = consumes
        self.produces = produces
        self.base_path = base_path
        self.swagger_base_url = swagger_base_url
        self.typeface_url = typeface_url
        self.config = config or SwaggerConfig()

        self.accepts: Dict[str, Dict[PathDefinition, bytes]] = {}
        self.collection_formats: Dict[str, Dict[PathDefinition, str]] = {}

        self.add({'GET'}, base_path + '/swagger.json', self.swagger_json)
        self.add({'GET'}, base_path + '/swagger', self.swagger_ui)

        self.swagger_dict: Dict[str, Any] = {
            'swagger': '2.0',
            'basePath': self.base_path,
            'info': {
                'title': self.title,
                'version': self.version,
                'description': self.description
            },
            'produces': [name.decode() for name in self.produces.keys()],
            'consumes': [name.decode() for name in self.consumes.keys()],
            "paths": {},
        }
        if tags:
            self.swagger_dict['tags'] = tags

    def add_rest(
            self,
            methods: AbstractSet[str],
            path: str,
            callback: RestCallback,
            *,
            accept: bytes = APPLICATION_JSON,
            content_type: bytes = APPLICATION_JSON,
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
                APPLICATION_JSON.
            content_type (bytes, optional): The content media type. Defaults
                to APPLICATION_JSON.
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
            self._add_swagger_path(
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
        sig = inspect.signature(callback)
        path_definition = PathDefinition(self.base_path + path)

        async def rest_callback(
                scope: Scope,
                _info: Info,
                matches: RouteMatches,
                content: Content
        ) -> HttpResponse:

            query_args = parse_qs(scope['query_string'].decode())
            body_args = await self._get_body_args(method, scope['headers'], content)

            args, kwargs = make_args(
                sig,
                matches,
                query_args,
                body_args
            )

            body = await callback(*args, **kwargs)

            accept = header.accept(scope['headers'])
            writer = self._make_writer(body, accept)
            headers = [
                (b'content-type', content_type)
            ]
            return status_code, headers, writer

        self.add_route(method, path_definition, rest_callback)

    def _add_swagger_path(
            self,
            method: str,
            path: str,
            callback: RestCallback,
            accept: bytes,
            content_type: bytes,
            collection_format: str,
            tags: Optional[List[str]],
            status_code: int,
            status_description: str
    ):
        path_definition = PathDefinition(path)
        swagger_path = make_swagger_path(path_definition)
        sig = inspect.signature(callback)
        docstring = docstring_parser.parse(inspect.getdoc(callback))
        params = make_swagger_parameters(
            method,
            accept,
            path_definition,
            sig,
            docstring,
            collection_format
        )

        response: Dict[str, Any] = {
            'description': status_description
        }

        response_schema = make_swagger_response_schema(sig)
        if response_schema is not None:
            response['schema'] = response_schema

        entry = {
            'parameters': params,
            'produces': [content_type.decode()],
            'consumes': [accept.decode()],
            'responses': {
                status_code: response
            }
        }

        if docstring:
            if docstring.short_description:
                entry['summary'] = docstring.short_description
            if docstring.long_description:
                entry['description'] = docstring.long_description
            error_responses = gather_error_responses(docstring)
            responses = cast(Dict[int, Dict[str, Any]], entry['responses'])
            responses.update(error_responses)

        if tags:
            entry['tags'] = tags

        paths: Dict[str, Any] = self.swagger_dict['paths']
        current_path: Dict[str, Any] = paths.setdefault(swagger_path, {})
        current_path[method.lower()] = entry

    def _make_writer(
            self,
            data: Optional[Any],
            accept: Optional[Mapping[bytes, float]]
    ) -> Optional[AsyncIterator[bytes]]:
        if data is None:
            return None
        # TODO: This is rubbish
        if not accept:
            serializer = self.produces[APPLICATION_JSON]
        else:
            for media_type in accept.keys():
                if media_type in self.produces:
                    serializer = self.produces[media_type]
                    break
            else:
                serializer = self.produces[APPLICATION_JSON]
        if not serializer:
            raise RuntimeError
        text = serializer(camelize_object(data))
        return text_writer(text)

    async def _get_body_args(
            self,
            method: str,
            headers: Headers,
            content: Content
    ) -> Any:
        if method in {'GET'}:
            return True, {}

        media_type, params = header.content_type(
            headers) or (b'', cast(Dict[bytes, Any], {}))
        deserializer = self.consumes.get(media_type)
        if deserializer is None:
            raise RuntimeError('No deserializer')
        body = await text_reader(content)
        return deserializer(body, media_type, params)

    async def swagger_json(
            self,
            _scope: Scope,
            _info: Info,
            _matches: RouteMatches,
            _content: Content
    ) -> HttpResponse:
        """The swagger JSON request handler"""
        spec = json.dumps(self.swagger_dict)
        return 200, [(b'content-type', b'application/json')], text_writer(spec)

    @bareasgi_jinja2.template('swagger.html')
    async def swagger_ui(
            self,
            _scope: Scope,
            _info: Info,
            _matches: RouteMatches,
            _content: Content
    ) -> Dict[str, Any]:
        """The swagger view request handler"""
        return {
            "title": self.title,
            "specs_url": "/api/1/swagger.json",
            'swagger_base_url': self.swagger_base_url,
            'typeface_url': self.typeface_url,
            "config": self.config
        }
