"""Argument builder"""

from inspect import Parameter, Signature
from typing import Any, Callable, Dict, List, Optional, Tuple

from inflection import camelize

import bareasgi_rest.typing_inspect as typing_inspect
from .types import Body
from .utils import is_body_type, get_body_type
from .protocol.json import from_json_value


def make_args(
        signature: Signature,
        matches: Dict[str, str],
        query: Dict[str, Any],
        body: Dict[str, Any],
        body_coercer: Callable[[Any, Any], Any]
) -> Tuple[Tuple[Any, ...], Dict[str, Any]]:
    """Make args and kwargs for the given signature from the route matches,
    query args and body.

    Args:
        signature (Signature): The function signature
        matches (Dict[str, str]): The route matches
        query (Dict[str, Any]): A dictionary built from the query string
        body (Dict[str, Any]): A dictionary built from the body
        body_coercer (Callable[[Any, Any], Any]): A coercer for the body

    Raises:
        KeyError: If a parameter was not found

    Returns:
        Tuple[Tuple[Any, ...], Dict[str, Any]]: A tuple for *args and **kwargs
    """

    kwargs: Dict[str, Any] = {}
    args: List[Any] = []

    body_parameter: Optional[Parameter] = None

    for parameter in signature.parameters.values():
        if is_body_type(parameter.annotation):
            body_type = get_body_type(parameter.annotation)
            value: Any = Body(body_coercer(body, body_type))
        else:
            camelcase_name = camelize(
                parameter.name,
                uppercase_first_letter=False
            )
            if camelcase_name in matches:
                value = from_json_value(
                    matches[camelcase_name],
                    parameter.annotation
                )
            elif camelcase_name in query:
                value = from_json_value(
                    query[camelcase_name],
                    parameter.annotation
                )
            elif body_parameter is None and camelcase_name in body:
                value = from_json_value(
                    body[camelcase_name],
                    parameter.annotation
                )
            elif typing_inspect.is_optional_type(parameter.annotation):
                value = None
            else:
                raise KeyError

        if (
                parameter.kind == Parameter.POSITIONAL_ONLY
                or parameter.kind == Parameter.POSITIONAL_OR_KEYWORD
        ):
            args.append(value)
        else:
            # Use the non-camelcased name
            kwargs[parameter.name] = value

    bound_args = signature.bind(*args, **kwargs)
    bound_args.apply_defaults()

    return bound_args.args, bound_args.kwargs
