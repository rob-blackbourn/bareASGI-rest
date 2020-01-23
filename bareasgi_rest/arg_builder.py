"""Argument builder"""

from inspect import Parameter, Signature
from typing import Any, Awaitable, Callable, Dict, List, Tuple

import bareasgi_rest.typing_inspect as typing_inspect

from .types import ArgDeserializer
from .utils import is_body_type, get_body_type


async def make_args(
        signature: Signature,
        matches: Dict[str, str],
        query: Dict[str, List[str]],
        body: Callable[[Any], Awaitable[Any]],
        arg_deserializer: ArgDeserializer
) -> Tuple[Tuple[Any, ...], Dict[str, Any]]:
    """Make args and kwargs for the given signature from the route matches,
    query args and body.

    Args:
        signature (Signature): The function signature
        matches (Dict[str, str]): The route matches
        query (Dict[str, Any]): A dictionary built from the query string
        body (Callable[[AsyncIterator[bytes], Any], Any]): Get the body
        arg_deserializer (ArgDeserializer): A deserializer for args

    Raises:
        KeyError: If a parameter was not found

    Returns:
        Tuple[Tuple[Any, ...], Dict[str, Any]]: A tuple for *args and **kwargs
    """

    kwargs: Dict[str, Any] = {}
    args: List[Any] = []

    for parameter in signature.parameters.values():
        if is_body_type(parameter.annotation):
            body_type = get_body_type(parameter.annotation)
            value: Any = await body(body_type)
        else:
            if parameter.name in matches:
                value = arg_deserializer(
                    matches[parameter.name],
                    parameter.annotation
                )
            elif parameter.name in query:
                if typing_inspect.is_list(parameter.annotation):
                    element_type, *_rest = typing_inspect.get_args(
                        parameter.annotation
                    )
                    value = [
                        arg_deserializer(
                            item,
                            element_type
                        )
                        for item in query[parameter.name]
                    ]
                else:
                    value = arg_deserializer(
                        query[parameter.name][0],
                        parameter.annotation
                    )

            elif typing_inspect.is_optional_type(parameter.annotation):
                value = None
            else:
                raise KeyError(parameter.name)

        if (
                parameter.kind == Parameter.POSITIONAL_ONLY
                or parameter.kind == Parameter.POSITIONAL_OR_KEYWORD
        ):
            args.append(value)
        else:
            kwargs[parameter.name] = value

    bound_args = signature.bind(*args, **kwargs)
    bound_args.apply_defaults()

    return bound_args.args, bound_args.kwargs
