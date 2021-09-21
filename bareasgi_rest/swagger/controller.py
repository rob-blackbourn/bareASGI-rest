"""A swagger controller"""

import logging
import json
from typing import (
    Any,
    Dict,
    Mapping,
    Optional
)

from bareasgi import text_writer
from bareasgi.basic_router.http_router import BasicHttpRouter
from baretypes import (
    RouteMatches,
    Scope,
    Info,
    Content,
    HttpResponse
)
import bareasgi_jinja2

from .repository import SwaggerRepository
from .config import SwaggerConfig

LOGGER = logging.getLogger(__name__)


class SwaggerController:
    """A swagger controller"""

    def __init__(
            self,
            title: str,
            base_path: str,
            swagger_base_url: str,
            typeface_url: str,
            config: Optional[SwaggerConfig],
            repo: SwaggerRepository
    ) -> None:
        self.title = title
        self.base_path = base_path
        self.swagger_base_url = swagger_base_url
        self.typeface_url = typeface_url
        self.config = config or SwaggerConfig()

        self.repo = repo

    def add_routes(self, router: BasicHttpRouter):
        """Add the swagger routes

        Args:
            router (BasicHttpRouter): The router
        """
        router.add(
            {'GET'},
            self.base_path + '/swagger.json',
            self._swagger_json
        )
        router.add(
            {'GET'},
            self.base_path + '/swagger',
            self._swagger_ui
        )

    async def _swagger_json(
            self,
            _scope: Scope,
            _info: Info,
            _matches: RouteMatches,
            _content: Content
    ) -> HttpResponse:
        spec = json.dumps(self.repo.definition)
        return 200, [(b'content-type', b'application/json')], text_writer(spec)

    @bareasgi_jinja2.template('swagger.html')
    async def _swagger_ui(
            self,
            _scope: Scope,
            _info: Info,
            _matches: RouteMatches,
            _content: Content
    ) -> Mapping[str, Any]:
        return {
            "title": self.title,
            "specs_url": self.base_path + "/swagger.json",
            'swagger_base_url': self.swagger_base_url,
            'typeface_url': self.typeface_url,
            "config": self.config
        }
