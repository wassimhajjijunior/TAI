from ..core.rabbitmq import can_connect, get_topology_metadata


SYSTEM_ENDPOINTS = [
  "GET /api/v1/system/messaging",
]


def get_messaging_status() -> dict[str, object]:
  connected, detail = can_connect()
  topology = get_topology_metadata()

  return {
    "rabbitmq": {
      "connected": connected,
      "detail": detail,
    },
    "topology": topology,
  }


SYSTEM_ROUTES = [
  ("GET", "/system/messaging", get_messaging_status),
]
