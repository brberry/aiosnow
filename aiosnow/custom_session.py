from typing import Any

from aiohttp import ClientSession

from aiosnow.config import ConfigSchema

REQUIRED_KEYS = [
    "client_id",
    "key_file",
    "subject",
]


def check_missing_keys(data: dict[str, Any]) -> list[str]:
    """
    Checks for missing keys in a dictionary.

    Args:
        data: The dictionary to check.

    Returns:
        A list of missing keys.
    """
    return [key for key in REQUIRED_KEYS if key not in data]


class CustomClientSession(ClientSession):
    def __init__(self, *args, config: ConfigSchema | None = None, **kwargs):
        self._config = config
        if not self._config.session.oauth:
            raise ValueError("OAuth settings not found in ConfigSchema.session")

        if missing_keys := check_missing_keys(self._config.session.oauth):
            raise ValueError(f"Oauth parameter has missing keys: {missing_keys}")

        super().__init__(*args, **kwargs)
