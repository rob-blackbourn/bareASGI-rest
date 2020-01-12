"""Tests for typing_import_ext"""

from datetime import datetime
from decimal import Decimal
import inspect
from typing import Any, Dict, List, Optional
try:
    from typing import TypedDict  # type:ignore
except:  # pylint: disable=bare-except
    from typing_extensions import TypedDict

import bareasgi_rest.typing_inspect_ext as typing_inspect
from bareasgi_rest.typing_inspect_ext import TypedDictMember

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

def bar(arg1: MockDict) -> str:
    return "hello"

def test_is_typed_dict():
    signature = inspect.signature(bar)
    arg1_param = signature.parameters["arg1"]
    assert typing_inspect.is_typed_dict(arg1_param.annotation)

def test_typed_dict_keys():
    signature = inspect.signature(bar)
    arg1_param = signature.parameters["arg1"]
    annotations = typing_inspect.typed_dict_annotation(arg1_param.annotation)
    assert annotations == {
        'arg_num1': TypedDictMember('arg_num1', str, TypedDictMember.empty),
        'arg_num2': TypedDictMember('arg_num2', List[int], TypedDictMember.empty),
        'arg_num3': TypedDictMember('arg_num3', datetime, TypedDictMember.empty),
        'arg_num4': TypedDictMember('arg_num4', Optional[Decimal], Decimal('1')),
        'arg_num5': TypedDictMember('arg_num5', Optional[float], None),
    }
