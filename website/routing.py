"""
This file associates WebSocket events with handler functions.

See https://channels.readthedocs.io/en/stable/getting-started.html#first-consumers
"""

from channels.routing import route
from .consumers import ws_connect, ws_message, ws_disconnect

channel_routing = [
    route("websocket.connect", ws_connect),
    route("websocket.receive", ws_message),
    route("websocket.disconnect", ws_disconnect),
]
