"""A Swagger Repository"""


from typing import (
    Any,
    Awaitable,
    Callable,
    Dict,
    List,
    Mapping,
    Optional
)

from bareasgi.basic_router.http_router import BasicHttpRouter, PathDefinition

from .entry import make_swagger_entry
from .paths import make_swagger_path

class SwaggerRepository:
    """A swagger repository"""

    def __init__(
            self,
            title: str,
            version: str,
            description: Optional[str],
            base_path: str,
            consumes: Optional[List[str]],
            produces: Optional[List[str]],
            tags: Optional[List[Mapping[str, Any]]]
    ) -> None:

        self.definition: Dict[str, Any] = {
            'swagger': '2.0',
            'basePath': base_path,
            'info': {
                'title': title,
                'version': version,
                'description': description
            },
            'produces': produces or [],
            'consumes': consumes or [],
            "paths": {},
        }
        if tags:
            self.definition['tags'] = tags


    def add(
            self,
            method: str,
            path: str,
            callback: Callable[..., Awaitable[Any]],
            accept: bytes,
            content_type: bytes,
            collection_format: str,
            tags: Optional[List[str]],
            status_code: int,
            status_description: str
    ):
        path_definition = PathDefinition(path)

        entry = make_swagger_entry(
            method,
            path_definition,
            callback,
            accept,
            content_type,
            collection_format,
            tags,
            status_code,
            status_description
        )

        swagger_path = make_swagger_path(path_definition)

        paths: Dict[str, Any] = self.definition['paths']
        current_path: Dict[str, Any] = paths.setdefault(swagger_path, {})
        current_path[method.lower()] = entry
