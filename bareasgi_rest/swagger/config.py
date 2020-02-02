"""Swagger Configuration"""

from typing import Callable, List, Optional


def _same_name(text: str) -> str:
    return text


class SwaggerOauth2Config:

    def __init__(
            self,
            client_id: str,
            realm: str,
            app_name: str,
            redirect_url: str
    ) -> None:
        """Swagger Oauth2 config

        Args:
            client_id (str): The client id
            realm (str): The realm
            app_name (str): The application name
            redirect_url (str): The redirect url
        """
        self.client_id = client_id
        self.realm = realm
        self.app_name = app_name
        self.redirect_url = redirect_url


class SwaggerConfig:

    def __init__(
        self,
        title: str = "The REST API",
        validator_url: Optional[str] = None,
        supported_submit_methods: Optional[List[str]] = None,
        display_operation_id: bool = False,
        display_request_duration: bool = False,
        doc_expansion: str = "list",
        oauth2: Optional[SwaggerOauth2Config] = None,
        serialize_key: Callable[[str], str] = _same_name,
        deserialize_key: Callable[[str], str] = _same_name
    ) -> None:
        """The Swagger UI Configuration

            Args:
                title (str, optional): The page title, defaults to "The REST API"
                validator_url (Optional[str], optional): The url of the validator,
                    defaults to None
                supported_submit_methods (Optional[List[str]], optional): The supported
                    submit methods, defaults to None
                display_operation_id (bool, optional): Whether operation ids should be
                    displayed, defaults to False
                display_request_duration (bool, optional): Whether the duration of the
                    request should be displayed, defaults to False
                doc_expansion (str, optional): How the methods should be displayed,
                    defaults to "list"
                oauth2 (Optional[SwaggerOauth2Config], optional): Optional oauth2
                    config, defaults to None
                serialize_key (Callable[[str], str]): The function to serialize keys
                deserialize_key (Callable[[str], str]): The function to deserialize keys

            """
        self.title = title
        self.validator_url = validator_url
        self.supported_submit_methods = supported_submit_methods
        self.display_operation_id = display_operation_id
        self.display_request_duration = display_request_duration
        self.doc_expansion = doc_expansion
        self.oauth2 = oauth2
        self.serialize_key = serialize_key
        self.deserialize_key = deserialize_key
