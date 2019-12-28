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
        ValueError: It doesn't actually raise this error

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

param1 = sig.parameters['arg1']
print(param1.annotation == str)
print(param1.annotation is str)

param2 = sig.parameters['arg2']
print(param2.annotation == List[int])
print(param2.annotation is List[int])

param3 = sig.parameters['arg3']
print(param3.annotation == datetime)
print(param3.annotation is datetime)

param4 = sig.parameters['arg4']
print(param4.annotation == Optional[Decimal])
print(param4.annotation is Optional[Decimal])

param5 = sig.parameters['arg5']
print(param5.annotation == Optional[float])
print(param5.annotation is Optional[float])


class Person(NamedTuple):
    first_name: str
    last_name: str


p1 = Person('Rob', 'Blackbourn')
p2 = Person('Ann-Marie', 'Dutton')
print(p1)
