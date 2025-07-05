"""Tests for swagger.py"""

from datetime import datetime
from decimal import Decimal
from typing import Annotated, Any, TypedDict

from jetblack_serialization import DefaultValue
from stringcase import camelcase, snakecase

from bareasgi_rest.swagger.config import SwaggerConfig

MOCK_SWAGGER_CONFIG = SwaggerConfig(
    serialize_key=camelcase,
    deserialize_key=snakecase
)


class MockDict(TypedDict):
    """A mock typed dict

    Args:
        arg_num1 (str): The first arg
        arg_num2 (list[int]): The second arg
        arg_num3 (datetime): The third arg
        arg_num4 (Decimal | None, optional): The fourth arg. Defaults to Decimal('1').
        arg_num5 (float | None, optional): The fifth arg. Defaults to None.
    """
    arg_num1: str
    arg_num2: list[int]
    arg_num3: datetime
    arg_num4: Annotated[Decimal | None, DefaultValue(Decimal('1'))]
    arg_num5: Annotated[float | None, DefaultValue(None)]


async def mock_func(
        arg_num1: str,
        *,
        arg_num2: list[int],
        arg_num3: datetime,
        arg_num4: Decimal | None = Decimal('1'),
        arg_num5: float | None = None
) -> dict[str, Any]:
    """A mock function

    A function to use in tests

    Args:
        arg_num1 (str): The first arg
        arg_num2 (list[int]): The second arg
        arg_num3 (datetime): The third arg
        arg_num4 (Decimal | None, optional): The fourth arg. Defaults to Decimal('1').
        arg_num5 (float | None, optional): The fifth arg. Defaults to None.

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
