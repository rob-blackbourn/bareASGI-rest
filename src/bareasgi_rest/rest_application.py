from typing import Any, Callable, Final, Sequence, cast

from jetblack_serialization.config import SerializerConfig

from bareasgi import (
    Application,
    HttpMiddlewares,
    HttpResponse,
    LifespanRequestHandler,
    WebSocketMiddlewares,
    WebSocketRouter,
)
from bareutils import text_writer
from bareutils import response_code

from .constants import DEFAULT_COLLECTION_FORMAT
from .rest_router import RestHttpRouter
from .types import ArgDeserializerFactory, DictSerializerConfig, RestCallback


DEFAULT_NOT_FOUND_RESPONSE: Final[HttpResponse] = HttpResponse(
    response_code.NOT_FOUND,
    [(b'content-type', b'text/plain')],
    text_writer('Not Found')
)


class RestApplication(Application):

    def __init__(
            self,
            *,
            middlewares: HttpMiddlewares | None = None,
            rest_router: RestHttpRouter | None = None,
            ws_middlewares: WebSocketMiddlewares | None = None,
            ws_router: WebSocketRouter | None = None,
            startup_handlers: list[LifespanRequestHandler] | None = None,
            shutdown_handlers: list[LifespanRequestHandler] | None = None,
            not_found_response: HttpResponse = DEFAULT_NOT_FOUND_RESPONSE,
            info: dict[str, Any] | None = None
    ) -> None:
        """Construct the application

        ```python
        from bareasgi import (
            Application,
            Scope,
            HttpRequest,
            HttpResponse,
            text_reader,
            text_writer
        )

        async def http_request_callback(request: HttpRequest) -> HttpResponse:
            text = await text_reader(request.body)
            return HttpResponse(
                200,
                [(b'content-type', b'text/plain')],
                text_writer('This is not a test')
            )

        import uvicorn

        app = Application()
        app.http_router.add({'GET', 'POST', 'PUT', 'DELETE'}, '/{path}', http_request_callback)

        uvicorn.run(app, port=9009)
        ```

        Args:
            middlewares (HttpMiddlewares | None, optional): Optional
                middleware callbacks. Defaults to None.
            rest_router (RestHttpRouter | None, optional): Optional router to for
                http routes. Defaults to None.
            ws_middlewares (WebSocketMiddlewares | None, optional):
                Optional middleware callbacks. Defaults to None.
            ws_router (WebSocketRouter | None, optional): Optional
                router for web routes. Defaults to None.
            startup_handlers (Optional[List[LifespanHandler]], optional): Optional
                handlers to run at startup. Defaults to None.
            shutdown_handlers (Optional[List[LifespanHandler]], optional): Optional
                handlers to run at shutdown. Defaults to None.
            not_found_response (Optional[HttpResponse], optional): Optional not
                found (404) response. Defaults to DEFAULT_NOT_FOUND_RESPONSE.
            info (dict[str, Any] | None, optional): Optional
                dictionary for user data. Defaults to None.
        """
        super().__init__(
            middlewares=middlewares,
            http_router=rest_router,
            ws_middlewares=ws_middlewares,
            ws_router=ws_router,
            startup_handlers=startup_handlers,
            shutdown_handlers=shutdown_handlers,
            not_found_response=not_found_response,
            info=info
        )

    @property
    def rest_router(self) -> RestHttpRouter:
        """Get the REST router

        Returns:
            RestHttpRouter: The REST router
        """
        return cast(RestHttpRouter, self.http_router)

    def on_rest_request(
            self,
            methods: set[str],
            path: str,
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
    ) -> Callable[[RestCallback], RestCallback]:
        """A decorator to add an http rest route handler to the application

        Args:
            methods (AbstractSet[str]): The http methods, e.g. {{'POST', 'PUT'}
            path (str): The path

        Returns:
            Callable[[HttpRequestCallback], HttpRequestCallback]: The decorated
                request.
        """
        def decorator(callback: RestCallback) -> Callable:
            self.rest_router.add_rest(
                methods,
                path,
                callback,
                consumes=consumes,
                produces=produces,
                collection_format=collection_format,
                tags=tags,
                status_code=status_code,
                status_description=status_description,
                serializer_config=serializer_config,
                arg_serializer_config=arg_serializer_config,
                arg_deserializer_factory=arg_deserializer_factory
            )
            return callback

        return decorator
