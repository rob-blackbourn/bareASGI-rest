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
    NamedTuple,
    Optional,
    Tuple,
    Type
)

import docstring_parser


async def mock_func(
        arg1: str,
        *,
        arg2: List[int],
        arg3: datetime,
        arg4: Optional[Decimal] = Decimal('1'),
        arg5: Optional[float] = None
) -> Dict[str, Any]:
    """A mock function

    A function to use in tests

    Args:
        arg1 (str): The first arg
        arg2 (List[int]): The second arg
        arg3 (datetime): The third arg
        arg4 (Optional[Decimal], optional): The fourth arg. Defaults to Decimal('1').
        arg5 (Optional[float], optional): The fifth arg. Defaults to None.

    Raises:
        HTTPError: 404, when a book is not found

    Returns:
        Dict[str, Any]: The args as a dictionary
    """
    return {
        'arg1': arg1,
        'arg2': arg2,
        'arg3': arg3,
        'arg4': arg4,
        'arg5': arg5
    }

sig = inspect.signature(mock_func)
docstring = docstring_parser.parse(inspect.getdoc(mock_func))

raises = docstring.raises
print(raises)


class Person(NamedTuple):
    first_name: str
    last_name: str


p1 = Person('Rob', 'Blackbourn')
p2 = Person('Ann-Marie', 'Dutton')
print(p1)
sig = inspect.signature(Person)
print(sig)

print(issubclass(Person, NamedTuple))
