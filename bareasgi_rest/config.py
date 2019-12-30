"""Configuration"""

from typing import List, NamedTuple, Optional


class SwaggerOauth2Config(NamedTuple):
    """Swagger Oauth2 config

    Args:
        client_id (str): The client id
        realm (str): The realm
        app_name (str): The application name
        redirect_url (str): The redirect url
    """
    client_id: str
    realm: str
    app_name: str
    redirect_url: str


class SwaggerConfig(NamedTuple):
    """The Swagger UI Configuration

    Args:
        NamedTuple ([type]): [description]
        validator_url (Optional[str], optional): The url of the validator, defaults to None
        supported_submit_methods (Optional[List[str]], optional): The supported submit methods, defaults to None
        display_operation_id (bool, optional): Whether operation ids should be displayed, defaults to False
        display_request_duration (bool, optional): Whether the duration of the request should be displayed, defaults to False
        doc_expansion (str, optional): How the methods should be displayed, defaults to "list"
        oauth2 (Optional[SwaggerOauth2Config], optional): Optional oauth2 config, defaults to None

    """
    validator_url: Optional[str] = None
    supported_submit_methods: Optional[List[str]] = None
    display_operation_id: bool = False
    display_request_duration: bool = False
    doc_expansion: str = "list"
    oauth2: Optional[SwaggerOauth2Config] = None
