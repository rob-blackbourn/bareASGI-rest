"""Ad-hoc experiments"""

from datetime import datetime
from decimal import Decimal
import inspect
from typing import Any, Dict, List, Optional
from typing_extensions import TypedDict

import bareasgi_rest.typing_inspect as typing_inspect

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

def func(
        arg1: MockDict,
        arg2: Dict[str, Any],
        arg3: Optional[MockDict],
        arg4: Optional[Dict[str, Any]]
) -> Optional[MockDict]:
    return None

def is_dict(annotation: Any) -> bool:
    return typing_inspect.get_origin(annotation) is dict and getattr(annotation, '_name', None) == 'Dict'

sig = inspect.signature(func)
arg1_param = sig.parameters['arg1']
arg2_param = sig.parameters['arg2']
arg3_param = sig.parameters['arg3']
arg4_param = sig.parameters['arg4']

print(is_dict(arg4_param.annotation))
print('here')