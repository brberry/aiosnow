from typing import Union

import aiohttp

from aiosnow.config import ConfigSchema
from aiosnow.exceptions import MissingClientAuthentication
from aiosnow.utils import get_url
from aiosnow.request import Response
from aiosnow.session import Session


class Client:
    """Client for communicating with ServiceNow

    Parses client config and provides a ClientSession factory.

    Args:
        address: Instance TCP address, example: my-instance.service-now.com
        basic_auth: Tuple of (username, password)
        use_ssl: Whether to use SSL
        verify_ssl: Whether to verify SSL certificates
        pool_size: Connection pool size
        response_cls: Custom Response class

    Attributes:
        config: Client configuration object
    """

    def __init__(
        self,
        address: Union[str, bytes],
        basic_auth: tuple = None,
        use_ssl: bool = True,
        verify_ssl: bool = None,
        pool_size: int = 100,
        response_cls: Response = None,
        session_cls: Session = None
    ):
        # Load config
        self.config = ConfigSchema(many=False).load(
            dict(
                address=address,
                session=dict(
                    basic_auth=basic_auth,
                    use_ssl=use_ssl or True,
                    verify_ssl=verify_ssl or True,
                )
            )
        )

        if self.config.session.basic_auth:
            self._auth = aiohttp.BasicAuth(*self.config.session.basic_auth)  # type: ignore
        else:
            raise MissingClientAuthentication("No known authentication methods was provided")

        self.session_cls = session_cls
        self.base_url = get_url(str(self.config.address), bool(use_ssl))
        self.response_cls = response_cls
        self.pool_size = pool_size

    def get_session(self):
        connector_args = dict(
            limit=self.pool_size
        )

        if self.config.session.use_ssl:
            connector_args["verify_ssl"] = self.config.session.verify_ssl

        session_cls = self.session_cls or Session

        return session_cls(
            auth=self._auth,
            skip_auto_headers=["Content-Type"],
            response_class=self.response_cls or Response,
            connector=aiohttp.TCPConnector(**connector_args)
        )
