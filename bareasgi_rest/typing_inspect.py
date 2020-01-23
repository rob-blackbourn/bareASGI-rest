"""Typing inspect extensions"""

import collections.abc
from inspect import Parameter
from typing import (
    Any,
    Callable,
    ClassVar,
    Dict,
    Generic,
    Optional,
    Tuple,
    TypeVar,
    Union
)
from typing import _GenericAlias  # type: ignore
try:
    # For 3.8
    # pylint: disable=unused-import
    from typing import TypedDict, _TypedDictMeta  # type: ignore
except ImportError:
    # For 3.7
    from typing_extensions import TypedDict, _TypedDictMeta  # type: ignore
from typing_extensions import Literal, Annotated, _AnnotatedAlias  # type: ignore


def is_typed_dict(annotation):
    """Test for a typed dictionary

    Args:
        annotation ([type]): The type annotation

    Returns:
        bool: True if the type annotation was for a typed dict
    """
    return isinstance(annotation, _TypedDictMeta)


def is_annotated_type(annotation):
    return isinstance(annotation, _AnnotatedAlias)


def get_annotated_type(annotation):
    return get_origin(annotation)


def get_annotated_type_metadata(annotation):
    return getattr(annotation, '__metadata__', None)


def is_generic_type(annotation):
    """Test if the given type is a generic type. This includes Generic itself, but
    excludes special typing constructs such as Union, Tuple, Callable, ClassVar.
    Examples::
        is_generic_type(int) == False
        is_generic_type(Union[int, str]) == False
        is_generic_type(Union[int, T]) == False
        is_generic_type(ClassVar[List[int]]) == False
        is_generic_type(Callable[..., T]) == False
        is_generic_type(Generic) == True
        is_generic_type(Generic[T]) == True
        is_generic_type(Iterable[int]) == True
        is_generic_type(Mapping) == True
        is_generic_type(MutableMapping[T, List[int]]) == True
        is_generic_type(Sequence[Union[str, bytes]]) == True
    """
    return (
        isinstance(annotation, type) and issubclass(annotation, Generic) or
        isinstance(annotation, _GenericAlias) and
        annotation.__origin__ not in (
            Union,
            tuple,
            ClassVar,
            collections.abc.Callable
        )
    )


def is_callable_type(annotation):
    """Test if the type is a generic callable type, including subclasses
    excluding non-generic types and callables.
    Examples::
        is_callable_type(int) == False
        is_callable_type(type) == False
        is_callable_type(Callable) == True
        is_callable_type(Callable[..., int]) == True
        is_callable_type(Callable[[int, int], Iterable[str]]) == True
        class MyClass(Callable[[int], int]):
            ...
        is_callable_type(MyClass) == True
    For more general tests use callable(), for more precise test
    (excluding subclasses) use::
        get_origin(tp) is collections.abc.Callable  # Callable prior to Python 3.7
    """
    return (
        annotation is Callable or isinstance(annotation, _GenericAlias) and
        annotation.__origin__ is collections.abc.Callable or
        isinstance(annotation, type) and issubclass(annotation, Generic) and
        issubclass(annotation, collections.abc.Callable)
    )


def is_tuple_type(annotation):
    """Test if the type is a generic tuple type, including subclasses excluding
    non-generic classes.
    Examples::
        is_tuple_type(int) == False
        is_tuple_type(tuple) == False
        is_tuple_type(Tuple) == True
        is_tuple_type(Tuple[str, int]) == True
        class MyClass(Tuple[str, int]):
            ...
        is_tuple_type(MyClass) == True
    For more general tests use issubclass(..., tuple), for more precise test
    (excluding subclasses) use::
        get_origin(tp) is tuple  # Tuple prior to Python 3.7
    """
    return (
        annotation is Tuple or isinstance(annotation, _GenericAlias) and
        annotation.__origin__ is tuple or
        isinstance(annotation, type) and issubclass(annotation, Generic) and
        issubclass(annotation, tuple)
    )


def is_union_type(annotation):
    """Test if the type is a union type. Examples::
        is_union_type(int) == False
        is_union_type(Union) == True
        is_union_type(Union[int, int]) == False
        is_union_type(Union[T, int]) == True
    """
    return (
        annotation is Union or
        isinstance(annotation, _GenericAlias) and annotation.__origin__ is Union
    )


def is_optional_type(annotation):
    """Test if the type is type(None), or is a direct union with it, such as Optional[T].
    NOTE: this method inspects nested `Union` arguments but not `TypeVar` definition
    bounds and constraints. So it will return `False` if
     - `tp` is a `TypeVar` bound, or constrained to, an optional type
     - `tp` is a `Union` to a `TypeVar` bound or constrained to an optional type,
     - `tp` refers to a *nested* `Union` containing an optional type or one of the above.
    Users wishing to check for optionality in types relying on type variables might wish
    to use this method in combination with `get_constraints` and `get_bound`
    """

    if annotation is type(None):
        return True
    elif is_union_type(annotation):
        return any(
            is_optional_type(tt)
            for tt in get_args(annotation, evaluate=True)
        )
    else:
        return False


def is_literal_type(annotation):
    """Test if the type represents a literal"""
    return (
        annotation is Literal or
        isinstance(annotation, _GenericAlias) and annotation.__origin__ is Literal
    )


def is_typevar(annotation):
    """Test if the type represents a type variable. Examples::
        is_typevar(int) == False
        is_typevar(T) == True
        is_typevar(Union[T, int]) == False
    """

    return isinstance(annotation, TypeVar)


def is_classvar(annotation):
    """Test if the type represents a class variable. Examples::
        is_classvar(int) == False
        is_classvar(ClassVar) == True
        is_classvar(ClassVar[int]) == True
        is_classvar(ClassVar[List[T]]) == True
    """
    return (
        annotation is ClassVar or
        isinstance(annotation, _GenericAlias)
        and annotation.__origin__ is ClassVar
    )


def get_origin(annotation):
    """Get the unsubscripted version of a type. Supports generic types, Union,
    Callable, and Tuple. Returns None for unsupported types. Examples::
        get_origin(int) == None
        get_origin(ClassVar[int]) == None
        get_origin(Generic) == Generic
        get_origin(Generic[T]) == Generic
        get_origin(Union[T, int]) == Union
        get_origin(List[Tuple[T, T]][int]) == list  # List prior to Python 3.7
    """
    if isinstance(annotation, _GenericAlias):
        return annotation.__origin__ if annotation.__origin__ is not ClassVar else None
    if annotation is Generic:
        return Generic
    return None


def get_parameters(annotation):
    """Return type parameters of a parameterizable type as a tuple
    in lexicographic order. Parameterizable types are generic types,
    unions, tuple types and callable types. Examples::
        get_parameters(int) == ()
        get_parameters(Generic) == ()
        get_parameters(Union) == ()
        get_parameters(List[int]) == ()
        get_parameters(Generic[T]) == (T,)
        get_parameters(Tuple[List[T], List[S_co]]) == (T, S_co)
        get_parameters(Union[S_co, Tuple[T, T]][int, U]) == (U,)
        get_parameters(Mapping[T, Tuple[S_co, T]]) == (T, S_co)
    """
    if (
            isinstance(annotation, _GenericAlias) or
            isinstance(annotation, type) and
            issubclass(annotation, Generic) and
            annotation is not Generic
    ):
        return annotation.__parameters__
    return ()


def _eval_args(args):
    """Internal helper for get_args."""
    res = []
    for arg in args:
        if not isinstance(arg, tuple):
            res.append(arg)
        elif is_callable_type(arg[0]):
            callable_args = _eval_args(arg[1:])
            if len(arg) == 2:
                res.append(Callable[[], callable_args[0]])
            elif arg[1] is Ellipsis:
                res.append(Callable[..., callable_args[1]])
            else:
                res.append(
                    Callable[list(callable_args[:-1]), callable_args[-1]])
        else:
            res.append(type(arg[0]).__getitem__(arg[0], _eval_args(arg[1:])))
    return tuple(res)


def get_args(annotation, evaluate=None):
    """Get type arguments with all substitutions performed. For unions,
    basic simplifications used by Union constructor are performed.
    On versions prior to 3.7 if `evaluate` is False (default),
    report result as nested tuple, this matches
    the internal representation of types. If `evaluate` is True
    (or if Python version is 3.7 or greater), then all
    type parameters are applied (this could be time and memory expensive).
    Examples::
        get_args(int) == ()
        get_args(Union[int, Union[T, int], str][int]) == (int, str)
        get_args(Union[int, Tuple[T, int]][str]) == (int, (Tuple, str, int))
        get_args(Union[int, Tuple[T, int]][str], evaluate=True) == \
                 (int, Tuple[str, int])
        get_args(Dict[int, Tuple[T, T]][Optional[int]], evaluate=True) == \
                 (int, Tuple[Optional[int], Optional[int]])
        get_args(Callable[[], T][int], evaluate=True) == ([], int,)
    """
    if evaluate is not None and not evaluate:
        raise ValueError('evaluate can only be True in Python 3.7')
    if isinstance(annotation, _GenericAlias):
        res = annotation.__args__
        if get_origin(annotation) is collections.abc.Callable and res[0] is not Ellipsis:
            res = (list(res[:-1]), res[-1])
        return res
    return ()


def get_bound(annotation):
    """Return the bound to a `TypeVar` if any.
    It the type is not a `TypeVar`, a `TypeError` is raised.
    Examples::
        get_bound(TypeVar('T')) == None
        get_bound(TypeVar('T', bound=int)) == int
    """

    if is_typevar(annotation):
        return getattr(annotation, '__bound__', None)
    else:
        raise TypeError("type is not a `TypeVar`: " + str(annotation))


def get_constraints(annotation):
    """Returns the constraints of a `TypeVar` if any.
    It the type is not a `TypeVar`, a `TypeError` is raised
    Examples::
        get_constraints(TypeVar('T')) == ()
        get_constraints(TypeVar('T', int, str)) == (int, str)
    """

    if is_typevar(annotation):
        return getattr(annotation, '__constraints__', ())
    else:
        raise TypeError("type is not a `TypeVar`: " + str(annotation))


def get_generic_type(obj):
    """Get the generic type of an object if possible, or runtime class otherwise.
    Examples::
        class Node(Generic[T]):
            ...
        type(Node[int]()) == Node
        get_generic_type(Node[int]()) == Node[int]
        get_generic_type(Node[T]()) == Node[T]
        get_generic_type(1) == int
    """

    gen_type = getattr(obj, '__orig_class__', None)
    return gen_type if gen_type is not None else type(obj)


def get_generic_bases(annotation):
    """Get generic base types of a type or empty tuple if not possible.
    Example::
        class MyClass(List[int], Mapping[str, List[int]]):
            ...
        MyClass.__bases__ == (List, Mapping)
        get_generic_bases(MyClass) == (List[int], Mapping[str, List[int]])
    """

    return getattr(annotation, '__orig_bases__', ())


class TypedDictMember:
    """The member of a typed dict"""

    empty = Parameter.empty

    def __init__(self, name: str, annotation: Any, default: Any = Parameter.empty) -> None:
        self.name = name
        self.annotation = annotation
        self.default = default

    def __eq__(self, other):
        return (
            isinstance(other, TypedDictMember) and
            self.name == other.name and
            self.annotation == other.annotation and
            self.default == other.default
        )


def typed_dict_annotation(obj: Any) -> Dict[str, TypedDictMember]:
    """Find the field annotations for a typed dict"""
    return {
        name: TypedDictMember(
            name,
            value,
            getattr(obj, name, TypedDictMember.empty)
        )
        for name, value in obj.__annotations__.items()
    }


def is_dict(annotation: Any) -> bool:
    """Return True if the annotation if for a Dict"""
    return (
        get_origin(annotation) is dict
        and getattr(annotation, '_name', None) == 'Dict'
    )


def is_list(annotation: Any) -> bool:
    """Return True if the annotation if for a List"""
    return (
        get_origin(annotation) is list
        and getattr(annotation, '_name', None) == 'List'
    )


def get_optional(annotation: Any) -> Optional[Any]:
    """Get the nested type annotation T for an Optional[T]"""
    if not is_optional_type(annotation):
        return None
    contained_type, *_rest = get_args(annotation)
    return contained_type


def is_optional_dict(annotation: Any) -> bool:
    """Return True if the type annotation is for an optional dict"""
    return is_optional_type(annotation) and is_dict(get_optional(annotation))


def is_optional_type_dict(annotation: Any) -> bool:
    """Return True if the type annotation is for an optional typed dict"""
    return is_optional_type(annotation) and is_typed_dict(get_optional(annotation))


def is_dict_like(annotation: Any) -> bool:
    """Return True for a dict or typed dict"""
    return is_dict(annotation) or is_typed_dict(annotation)


def is_possibly_optional_dict_like(annotation: Any) -> bool:
    """Return true for dict like"""
    return is_dict_like(annotation) or is_dict_like(get_optional(annotation))
