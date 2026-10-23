"""Compatibility import; HTTP transport lives in the presentation layer."""

from api.presentation.http import (  # noqa: F401
    ChatGateway,
    LocalBridge,
    make_http_server,
    make_socket_server,
)
