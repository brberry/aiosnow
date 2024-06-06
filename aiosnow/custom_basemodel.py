import time
import typing
import uuid
from pathlib import Path
from typing import Any, cast

import jwt
from yarl import URL

from aiosnow import TableModel
from aiosnow.custom_session import CustomClientSession
from aiosnow.query import Condition, Selector, select
from aiosnow.request import Response, methods


class CustomBaseModel(TableModel):
    @property
    def _stats_url(self) -> Any:
        return f"{self._client.base_url}/api/now/stats/{self._table_name}"

    async def request(self, method: str, *args: Any, **kwargs: Any) -> Response:
        if "Authorization" not in self._session.headers:
            await self._get_token()
        # else:
        #     print(f"He says they've already GOT one!")
        return await super().request(method, *args, **kwargs)

    async def _get_token(self, refresh: bool = False) -> None:
        session = cast(CustomClientSession, self._session)
        if not session._config:
            raise ValueError("config not set")
        if not session._config.session:
            raise ValueError("session not set in config")
        oauth: dict = session._config.session.oauth  # type: ignore[assignment]
        priv_key = Path(oauth["key_file"]).read_bytes()
        if oauth.get("key_passphrase"):
            from cryptography.hazmat.backends import default_backend
            from cryptography.hazmat.primitives import serialization

            private_key = serialization.load_pem_private_key(
                priv_key,
                password=bytes(oauth.get("key_passphrase"), "utf-8"),  # type: ignore[arg-type]
                backend=default_backend(),
            )
        else:
            private_key = priv_key  # type: ignore[assignment]

        now = int(time.time())

        # Generate a unique JWT ID (jti)
        jwt_id = str(uuid.uuid4())

        # JWT payload
        payload = {
            "iss": oauth["client_id"],
            "aud": oauth["client_id"],
            "sub": oauth["subject"],
            "iat": now,
            "exp": now + 3600,
            "nbf": now,  # Not before time in UTC (valid immediately)
            "jti": jwt_id,
        }

        assertion = jwt.encode(payload, private_key, algorithm="RS256")  # type: ignore[arg-type]
        token_data = {"grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer", "assertion": assertion}
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Cache-Control": "no-cache",
        }
        token_url = URL(f"https://{session._config.address}") / "oauth_token.do"

        # asyncio.get_event_loop().run_until_complete(self._post_token(token_url, token_data, headers))
        async with session.post(token_url, data=token_data, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                await self._update_session(data)
            else:
                print(f"Error: {response.status}")

        return

    async def _update_session(self, token: dict[str, Any]) -> None:
        # print(f"Token: {token}")
        self._token = token
        self._session_id = self._token.get("access_token", None)
        self._session.headers["Authorization"] = f"Bearer {self._session_id}"
        # print(f"Set Authorization to {self._session.headers['Authorization']}")

    async def count(self, selection: Selector | Condition | str, **kwargs: Any) -> int:
        """Buffered many

        Fetch and store the entire result in memory.

        Note: It's recommended to use the stream method when dealing with a
        large number of records.

        Keyword Args:
            selection: Aiosnow-compatible query
            limit (int): Maximum number of records to return
            offset (int): Starting record index

        Returns:
            count (int) of query results
            -1 if not found
        """

        response = await self.request(
            methods.GET,
            query=select(selection).sysparms,
            nested_fields=self._nested_fields,
            resolve=True,
            url=self._stats_url,
            count=True,
            decode=False,
            **kwargs,
        )
        await response.load_document()
        if typing.TYPE_CHECKING:
            assert isinstance(response.data, dict)
        return response.data.get("stats", {}).get("count", -1)
