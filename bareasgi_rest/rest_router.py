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
    List,
    Mapping,
    Optional,
    Tuple,
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
from .swagger import make_swagger_path, make_swagger_parameters, gather_error_responses

LOGGER = logging.getLogger(__name__)

DEFAULT_SWAGGER_BASE_URL = "https://cdnjs.cloudflare.com/ajax/libs/swagger-ui/3.4.0"
DEFAULT_TYPEFACE_URL = "https://fonts.googleapis.com/css?family=Roboto:300,400,500,700&display=swap"

APPLICATION_JSON = b'application/json'


def to_json(obj: Any) -> str:
    return json.dumps(obj, cls=JSONEncoderEx)


def from_json(text: str, _media_type: bytes, _params: Dict[bytes, bytes]) -> Any:
    return json.loads(text, object_hook=as_datetime)


def from_query_string(text: str, _media_type: bytes, _params: Dict[bytes, bytes]) -> Any:
    return parse_qs(text)


def from_form_data(text: str, _media_type: bytes, params: Dict[bytes, bytes]) -> Any:
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
    b'application/json': from_json,
    b'*/*': from_json,
    b'application/x-www-form-urlencoded': from_query_string,
    b'multipart/form-data': from_form_data

}

Serializer = Callable[[Any], str]
DictProduces = Dict[bytes, Serializer]
DEFAULT_PRODUCES: DictProduces = {
    b'application/json': to_json,
    b'*/*': to_json
}

RestCallback = Callable[..., Awaitable[Any]]

DEFAULT_COLLECTION_FORMAT = 'multi'
DEFAULT_RESPONSES = {
    200: {
        'description': 'OK'
    }
}


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
            swagger_base_url: Optional[str] = None,
            typeface_url: Optional[str] = None
    ) -> None:
        super().__init__(not_found_response)
        self.title = title
        self.version = version
        self.description = description
        self.consumes = consumes
        self.produces = produces
        self.base_path = base_path
        self.swagger_base_url = swagger_base_url or DEFAULT_SWAGGER_BASE_URL
        self.typeface_url = typeface_url or DEFAULT_TYPEFACE_URL

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
            "responses": {
                "ParseError": {
                    "description": "When a mask can't be parsed"
                },
                "MaskError": {
                    "description": "When any error occurs on mask"
                }
            },
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
            accept=APPLICATION_JSON,
            content_type=APPLICATION_JSON,
            collection_format=DEFAULT_COLLECTION_FORMAT,
            tags: Optional[List[str]] = None,
            status_code: int = 200,
            status_description: str = 'OK'
    ) -> None:
        """Add a rest callback"""
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
        entry = {
            'parameters': params,
            'produces': [content_type.decode()],
            'consumes': [accept.decode()],
            'responses': {
                status_code: {
                    'description': status_description
                }
            }
        }
        if docstring:
            if docstring.short_description:
                entry['summary'] = docstring.short_description
            if docstring.long_description:
                entry['description'] = docstring.long_description
            error_responses = gather_error_responses(docstring)
            responses: Dict[int, Dict[str, Any]] = entry['responses']
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
        try:
            spec = json.dumps(self.swagger_dict)
            return 200, [(b'content-type', b'application/json')], text_writer(spec)
        except Exception as error:
            print(error)
            return 500

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
            "swagger_validator_url": "https://validator.swagger.io/validator",
            "swagger_supported_submit_methods": None,
            "swagger_operation_id": False,
            "swagger_request_duration": None,
            "swagger_doc_expansion": "none",
            'typeface_url': self.typeface_url,
        }
