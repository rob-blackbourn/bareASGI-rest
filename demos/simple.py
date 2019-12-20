"""
A simple request handler.
"""

from datetime import datetime
import logging
from typing import Dict, Any

from bareasgi import (
    Application,
    Scope,
    Info,
    RouteMatches,
    Content,
    HttpResponse,
    text_writer
)
from bareasgi_rest import RestHttpRouter

logging.basicConfig(level=logging.DEBUG)


async def http_request_callback(
        _scope: Scope,
        _info: Info,
        _matches: RouteMatches,
        _content: Content
) -> HttpResponse:
    """A request handler which returns some text"""
    return 200, [(b'content-type', b'text/plain')], text_writer('This is not a test')

async def rest_callback(
        name: str,
        count: int
) -> Dict[str, Any]:
    """A request handler which returns some text"""
    return {
        'name': name,
        'count': count
    }


if __name__ == "__main__":
    import uvicorn

    app = Application(http_router=RestHttpRouter(None))
    app.http_router.add({'GET'}, '/foo', http_request_callback)
    app.http_router.add_rest({'GET'}, '/bar', rest_callback)

    uvicorn.run(app, port=9009)
