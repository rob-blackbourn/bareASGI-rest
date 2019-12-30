"""Adhoc typing"""

import inspect
from typing import Dict, Any, List, Callable, NamedTuple, Optional

import docstring_parser
from typing_extensions import TypedDict
import typing_inspect


class Point2D(TypedDict, total=False):
    """A class for representing 2D points

    Args:
        x (int): The x coordinate
        y (int): The y coordinate
        label (str, optional): The label
    """
    x: int
    y: int
    label: str


point = Point2D(x=1, y=2, label='hello')
print(point)


class Point3D(NamedTuple):
    """A class for representing 2D points

    Args:
        x (int): The x coordinate
        y (int): The y coordinate
        z (int): The z coordinate
        label (str, optional): The label
    """
    x: int
    y: int
    z: int
    label1: Optional[str] = None
    label2: Optional[str] = None


point3d = Point3D(1, 2, 3, label2='hello')
print(point3d)
