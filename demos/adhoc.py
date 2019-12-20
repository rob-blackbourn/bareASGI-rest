"""Ad hoc"""

import asyncio
from datetime import datetime
from decimal import Decimal
import inspect
from inspect import Parameter, Signature
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Tuple,
    Type
)
import pytypes

def is_supported_optional(annotation) -> bool:
    return (
        pytypes.is_subtype(annotation, Optional[str]) or
        pytypes.is_subtype(annotation, Optional[int]) or
        pytypes.is_subtype(annotation, Optional[float]) or
        pytypes.is_subtype(annotation, Optional[Decimal]) or
        pytypes.is_subtype(annotation, Optional[datetime])
    )
    
def coerce(value: str, annotation: Any) -> Any:
    if type(annotation) is type:
        single_value = value[0] if isinstance(value, list) else value
        if annotation is str:
            return single_value
        elif annotation is int:
            return int(single_value)
        elif annotation is float:
            return float(single_value)
        elif annotation is Decimal:
            return Decimal(single_value)
        elif annotation is datetime:
            return datetime.fromisoformat(single_value)
        else:
            raise TypeError
    if pytypes.is_subtype(annotation, Optional[str]):
        return None if not value else coerce(value, str)
    elif pytypes.is_subtype(annotation, Optional[int]):
        return None if not value else coerce(value, int)
    elif pytypes.is_subtype(annotation, Optional[float]):
        return None if not value else coerce(value, float)
    elif pytypes.is_subtype(annotation, Optional[Decimal]):
        return None if not value else coerce(value, Decimal)
    elif pytypes.is_subtype(annotation, Optional[datetime]):
        return None if not value else coerce(value, datetime)
    elif pytypes.is_subtype(annotation, List[str]):
        contained_type: Any = str
    elif pytypes.is_subtype(annotation, List[int]):
        contained_type = int
    elif pytypes.is_subtype(annotation, List[float]):
        contained_type = float
    elif pytypes.is_subtype(annotation, List[Decimal]):
        contained_type = Decimal
    elif pytypes.is_subtype(annotation, List[datetime]):
        contained_type = datetime
    else:
        raise TypeError
    return [coerce(item, contained_type) for item in value]


def make_args(
        sig: Signature,
        matches: Dict[str, str],
        query: Dict[str, Any]
) -> Tuple[Tuple[Any, ...], Dict[str, Any]]:
    """Make args"""
    kwargs: Dict[str, Any] = {}
    args: List[Any] = []

    for param in sig.parameters.values():
        if param.name in matches:
            value = coerce(matches[param.name], param.annotation)
        elif param.name in query:
            value = coerce(query[param.name], param.annotation)
        elif is_supported_optional(param.annotation):
            continue
        else:
            raise KeyError

        if param.kind == Parameter.POSITIONAL_ONLY or param.kind == Parameter.POSITIONAL_OR_KEYWORD:
            args.append(value)
        else:
            kwargs[param.name] = value

    bound_args = sig.bind(*args, **kwargs)
    bound_args.apply_defaults()

    return bound_args.args, bound_args.kwargs

async def foo(
        arg1: str,
        *,
        arg2: List[int],
        arg3: datetime,
        arg4: Optional[Decimal] = Decimal('1'),
        arg5: Optional[float] = None
) -> Dict[str, Any]:
    return {
        'arg1': arg1,
        'arg2': arg2,
        'arg3': arg3,
        'arg4': arg4,
        'arg5': arg5
    }

async def main():
    foo_sig = inspect.signature(foo)
    foo_matches = {
        'arg1': 'hello'
    }
    foo_query = {
        'arg2': ['1', '2'],
        'arg3': '1967-08-12T00:00:00',
        'arg4': '3.142'
    }
    foo_args, foo_kwargs = make_args(foo_sig, foo_matches, foo_query)
    print (foo_args, foo_kwargs)
    foo_return = await foo(*foo_args, **foo_kwargs)
    print(foo_return)

if __name__ == '__main__':
    asyncio.run(main())
