"""Adhoc typing"""

import inspect
from typing import Dict, Any, List, Callable, Optional

import docstring_parser
from typing_extensions import TypedDict
import typing_inspect


class Point2D(TypedDict):
    """A class for representing 2D points

    Args:
        x (int): The x coordinate
        y (int): The y coordinate
        label (str): The label
    """
    x: int
    y: int
    label: str


doc = inspect.getdoc(Point2D)
ds = docstring_parser.parse(doc, docstring_parser.Style.google)
print(ds)


def func() -> Point2D:
    """A test function

    Returns:
        Point2D: A 2D point
    """
    return Point2D(x=1, y=2, label="hello")


def func2() -> List[Point2D]:
    """A test function

    Returns:
        List[Point2D]: A 2D point
    """
    return [Point2D(x=1, y=2, label="hello")]


def func3() -> Dict[str, Any]:
    """A test function

    Returns:
        Dict[str, Any]: A 2D point
    """
    return dict(x=1, y=2, label="hello")


def func4() -> List[Dict[str, Any]]:
    """A test function

    Returns:
        List[Dict[str, Any]]: A 2D point
    """
    return [dict(x=1, y=2, label="hello")]


def func5() -> int:
    """A test function

    Returns:
        int: A 2D point
    """
    return 42


def func6() -> None:
    """A test function

    Returns:
        int: A 2D point
    """


sig = inspect.signature(func)
args = typing_inspect.get_args(sig.return_annotation)
print(sig.return_annotation)

sig2 = inspect.signature(func2)
args2 = typing_inspect.get_args(sig2.return_annotation)
print(sig2.return_annotation)

sig3 = inspect.signature(func3)
args3 = typing_inspect.get_args(sig3.return_annotation)
print(sig3.return_annotation)


def make_swagger_return_schema(
        callback: Callable[..., Any]
) -> Optional[Dict[str, Any]]:
    sig = inspect.signature(callback)
    origin = typing_inspect.get_origin(sig.return_annotation)
    if not origin and issubclass(sig.return_annotation, dict):
        # could be a typed dict
        annotations = getattr(sig.return_annotation, '__annotations__', None)
        if isinstance(annotations, dict):
            docstring = docstring_parser.parse(
                inspect.getdoc(sig.return_annotation))
            return {
                'type': 'object',
                'properties': {
                    name: {
                        'type': value
                    }
                    for name, value in annotations.items()
                }
            }
        else:
            return None
    elif origin and origin is list:
        # could be a list of typed dicts
        args = typing_inspect.get_args(sig.return_annotation)
        if len(args) != 1:
            return None
        nested_type = args[0]
        nested_origin = typing_inspect.get_origin(nested_type)
        if nested_origin and nested_origin is dict:
            # List[Dict]
            return None
        elif not nested_origin and issubclass(nested_type, dict):
            # A TypedDict
            annotations = getattr(nested_type, '__annotations__', None)
            if isinstance(annotations, dict):
                # List[TypedDict]
                docstring = docstring_parser.parse(inspect.getdoc(nested_type))
                return {
                    'type': 'array',
                    'properties': {
                        name: {
                            'type': value
                        }
                        for name, value in annotations.items()
                    }
                }
            else:
                # List[Dict]
                return None
        else:
            # List
            return None
    elif origin and origin is dict:
        # A Dict
        return None
    elif sig.return_annotation is None:
        # None
        return None

    # Something else
    return None


rt1 = make_swagger_return_schema(func)
rt2 = make_swagger_return_schema(func2)
rt3 = make_swagger_return_schema(func3)
rt4 = make_swagger_return_schema(func4)
rt5 = make_swagger_return_schema(func5)
rt6 = make_swagger_return_schema(func6)
