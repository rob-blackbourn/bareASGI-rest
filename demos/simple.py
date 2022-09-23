"""
A simple request handler.

Try the following endpoints:

- http://localhost:9009/named?name=hello&count=1
- http://localhost:9009/bar/hello/1
"""

import logging
from typing import Dict, Any

from bareasgi import Application, HttpRequest, HttpResponse, text_writer
from bareasgi_rest import RestHttpRouter, add_swagger_ui

logging.basicConfig(level=logging.DEBUG)


async def http_request_callback(_request: HttpRequest) -> HttpResponse:
    """A request handler which returns some text"""
    headers = [(b'content-type', b'text/plain')]
    body = text_writer('This is not a test')
    return HttpResponse(200, headers, body)


async def rest_callback(name: str, count: int) -> Dict[str, Any]:
    """A request handler which returns some text"""
    return {
        'name': name,
        'count': count
    }


if __name__ == "__main__":
    import uvicorn

    http_router = RestHttpRouter("Simple", "1")
    app = Application(http_router=http_router)

    add_swagger_ui(app)
    
    # A non-rest endpoint.
    http_router.add({'GET'}, '/foo', http_request_callback)
    # For http://localhost:9009/bar/hello/1
    http_router.add_rest({'GET'}, '/bar/{name:str}/{count:int}', rest_callback)
    # For http://localhost:9009/named?name=hello&count=1
    http_router.add_rest({'GET'}, '/named', rest_callback)

    uvicorn.run(app, port=9009)
