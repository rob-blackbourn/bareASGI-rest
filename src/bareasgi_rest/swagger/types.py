from typing import Any, Literal, Mapping, NotRequired, TypedDict


type SwaggerType = Literal[
    'string',
    'boolean',
    'integer',
    'number',
    'object',
    'array'
]


class SwaggerProperty(TypedDict):
    """A swagger property"""

    type: SwaggerType
    format: NotRequired[str]
    collectionFormat: NotRequired[str]
    items: NotRequired['SwaggerProperty']
    properties: NotRequired[dict[str, 'SwaggerProperty']]
    enum: NotRequired[list[str]]
    name: NotRequired[str]
    description: NotRequired[str]
    default: NotRequired[Any]


SwaggerParameter = TypedDict('SwaggerParameter', {
    'type': NotRequired[SwaggerType],
    'format': NotRequired[str],
    'collectionFormat': NotRequired[str],
    'items': NotRequired[SwaggerProperty],
    'properties': NotRequired[dict[str, SwaggerProperty]],
    'enum': NotRequired[list[str]],
    'name': NotRequired[str],
    'description': NotRequired[str],
    'default': NotRequired[Any],
    'in': str,
    'required': NotRequired[bool],
    'schema': NotRequired[SwaggerProperty]
})


class SwaggerResponse(TypedDict):
    """A swagger response"""

    description: str
    schema: NotRequired[SwaggerProperty]


class SwaggerInfo(TypedDict):
    """A swagger info object"""

    title: str
    version: str
    description: str | None


class SwaggerDefinition(TypedDict):
    """A swagger definition"""

    swagger: str
    basePath: str
    info: SwaggerInfo
    produces: list[str]
    consumes: list[str]
    paths: dict[str, Any]
    tags: NotRequired[list[Mapping[str, Any]]]


class SwaggerEntry(TypedDict):
    """A swagger entry"""

    parameters: list[SwaggerParameter]
    produces: list[str]
    consumes: list[str]
    responses: dict[int, SwaggerResponse]
    summary: NotRequired[str]
    description: NotRequired[str]
    tags: NotRequired[list[str]]
