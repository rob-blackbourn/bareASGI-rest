"""A Swagger Repository"""


from typing import (
    Any,
    Dict,
    List,
    Mapping,
    Optional
)

from bareasgi.basic_router.http_router import PathDefinition

from ..types import RestCallback

from .config import SwaggerConfig
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
            tags: Optional[List[Mapping[str, Any]]],
            config: SwaggerConfig
    ) -> None:
        self.config = config

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
            path_definition: PathDefinition,
            callback: RestCallback,
            consumes: List[bytes],
            produces: List[bytes],
            collection_format: str,
            tags: Optional[List[str]],
            status_code: int,
            status_description: str
    ):
        """Add a swagger entry

        Args:
            method (str): The HTTP method
            path_definition (PathDefinition): The router path
            callback (RestCallback): The callback
            consumes (List[bytes]): The accept header
            produces (List[bytes]): The content type
            collection_format (str): The collection format
            tags (Optional[List[str]]): Optional tags
            status_code (int): The ok status code
            status_description (str): The ok status description
        """

        entry = make_swagger_entry(
            method,
            path_definition,
            callback,
            consumes,
            produces,
            collection_format,
            tags,
            status_code,
            status_description,
            self.config
        )

        swagger_path = make_swagger_path(path_definition)

        paths: Dict[str, Any] = self.definition['paths']
        current_path: Dict[str, Any] = paths.setdefault(swagger_path, {})
        current_path[method.lower()] = entry
