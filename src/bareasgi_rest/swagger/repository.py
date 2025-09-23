"""A Swagger Repository"""


from typing import (
    Any,
    Mapping,
    Sequence,
)

from bareasgi.basic_router.path_definition import PathDefinition

from ..types import RestCallback

from .config import SwaggerConfig
from .entry import make_swagger_entry
from .paths import make_swagger_path
from .types import SwaggerDefinition


class SwaggerRepository:
    """A swagger repository"""

    def __init__(
            self,
            title: str,
            version: str,
            description: str | None,
            base_path: str,
            consumes: list[str] | None,
            produces: list[str] | None,
            tags: list[Mapping[str, Any]] | None,
            config: SwaggerConfig
    ) -> None:
        self.config = config

        self.definition: SwaggerDefinition = {
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
            consumes: Sequence[bytes],
            produces: Sequence[bytes],
            collection_format: str,
            tags: list[str] | None,
            status_code: int,
            status_description: str
    ) -> None:
        """Add a swagger entry

        Args:
            method (str): The HTTP method
            path_definition (PathDefinition): The router path
            callback (RestCallback): The callback
            consumes (Sequence[bytes]): The accept header
            produces (Sequence[bytes]): The content type
            collection_format (str): The collection format
            tags (list[str] | None): Optional tags
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

        paths: dict[str, Any] = self.definition['paths']
        current_path: dict[str, Any] = paths.setdefault(swagger_path, {})
        current_path[method.lower()] = entry
