"""A swagger controller"""

import logging
import json
from typing import Optional

from bareasgi import HttpRequest, HttpResponse, text_writer
from bareasgi.basic_router.http_router import BasicHttpRouter
from bareasgi_jinja2 import Jinja2TemplateProvider
from bareutils import response_code

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

    async def _swagger_json(self, _request: HttpRequest) -> HttpResponse:
        body = text_writer(json.dumps(self.repo.definition))
        headers = [(b'content-type', b'application/json')]
        return HttpResponse(response_code.OK, headers, body)

    async def _swagger_ui(self, request: HttpRequest) -> HttpResponse:
        return await Jinja2TemplateProvider.apply(
            request,
            'swagger.html',
            {
                "title": self.title,
                "specs_url": self.base_path + "/swagger.json",
                'swagger_base_url': self.swagger_base_url,
                'typeface_url': self.typeface_url,
                "config": self.config
            }
        )
