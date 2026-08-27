"""Utility functions"""

from bareasgi.basic_router.path_definition import PathDefinition


def make_swagger_path(path_definition: PathDefinition) -> str:
    """Make a path compatible with swagger"""
    swagger_path = '/' + '/'.join(
        '{' + segment.name + '}' if segment.is_variable else segment.name
        for segment in path_definition.segments
    )
    if path_definition.ends_with_slash:
        swagger_path += '/'
    return swagger_path
