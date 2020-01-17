"""Tests for swagger.py"""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
try:
    from typing import TypedDict  # type:ignore
except:  # pylint: disable=bare-except
    from typing_extensions import TypedDict


class MockDict(TypedDict):
    """A mock typed dict

    Args:
        arg_num1 (str): The first arg
        arg_num2 (List[int]): The second arg
        arg_num3 (datetime): The third arg
        arg_num4 (Optional[Decimal], optional): The fourth arg. Defaults to Decimal('1').
        arg_num5 (Optional[float], optional): The fifth arg. Defaults to None.
    """
    arg_num1: str
    arg_num2: List[int]
    arg_num3: datetime
    arg_num4: Optional[Decimal] = Decimal('1')
    arg_num5: Optional[float] = None


async def mock_func(
        arg_num1: str,
        *,
        arg_num2: List[int],
        arg_num3: datetime,
        arg_num4: Optional[Decimal] = Decimal('1'),
        arg_num5: Optional[float] = None
) -> Dict[str, Any]:
    """A mock function

    A function to use in tests

    Args:
        arg_num1 (str): The first arg
        arg_num2 (List[int]): The second arg
        arg_num3 (datetime): The third arg
        arg_num4 (Optional[Decimal], optional): The fourth arg. Defaults to Decimal('1').
        arg_num5 (Optional[float], optional): The fifth arg. Defaults to None.

    Raises:
        ValueError: It doesn't actually raise this error

    Returns:
        Dict[str, Any]: The args as a dictionary
    """
    return {
        'arg_num1': arg_num1,
        'arg_num2': arg_num2,
        'arg_num3': arg_num3,
        'arg_num4': arg_num4,
        'arg_num5': arg_num5
    }
