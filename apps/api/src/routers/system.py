from ..core.rabbitmq import can_connect, get_topology_metadata
from ..core.supabase_client import get_supabase_settings

SYSTEM_ENDPOINTS = [
    "GET /api/v1/system/messaging",
    "GET /api/v1/system/messaging/topology",
    "GET /api/v1/system/health",
    "GET /api/v1/system/activity",
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


def get_messaging_topology() -> dict[str, object]:
    topology = get_topology_metadata()
    queues_raw = topology.get("queues", {})
    return {
        "queues": [
            {"name": name, "messages": 0, "consumers": 0} for name in queues_raw
        ],
        "exchanges": [
            {
                "name": topology.get("exchange", ""),
                "type": topology.get("exchange_type", ""),
            }
        ],
    }


def get_activity_logs(
    tenant_id: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> dict[str, object]:
    return {
        "items": [],
        "total": 0,
        "limit": limit,
        "offset": offset,
    }


def get_system_health() -> dict[str, object]:
    from importlib import import_module
    import os

    status = "ok"
    checks: dict[str, object] = {}

    try:
        settings = get_supabase_settings()
        module = import_module("supabase")
        create_client = getattr(module, "create_client")
        client = create_client(settings.url, settings.service_role_key)
        result = client.table("tenants").select("id").limit(1).execute()
        data = getattr(result, "data", None)
        if data is not None:
            checks["supabase"] = {"status": "connected"}
        else:
            checks["supabase"] = {"status": "error", "detail": "no data returned"}
            status = "degraded"
    except Exception as error:
        checks["supabase"] = {"status": "error", "detail": str(error)[:200]}
        status = "degraded"

    try:
        connected, detail = can_connect()
        if connected:
            checks["rabbitmq"] = {"status": "connected"}
        else:
            checks["rabbitmq"] = {"status": "error", "detail": detail}
            status = "degraded"
    except Exception as error:
        checks["rabbitmq"] = {"status": "error", "detail": str(error)[:200]}
        status = "degraded"

    redis_url = os.getenv("REDIS_URL", "")
    if redis_url:
        try:
            redis_module = import_module("redis")
            Redis = getattr(redis_module, "Redis")
            r = Redis.from_url(redis_url, socket_timeout=2.0)
            r.ping()
            checks["redis"] = {"status": "connected"}
            r.close()
        except Exception as error:
            checks["redis"] = {"status": "error", "detail": str(error)[:200]}
            status = "degraded"
    else:
        checks["redis"] = {"status": "not_configured"}

    return {
        "status": status,
        "checks": checks,
    }


SYSTEM_ROUTES = [
    ("GET", "/system/messaging", get_messaging_status),
    ("GET", "/system/messaging/topology", get_messaging_topology),
    ("GET", "/system/health", get_system_health),
    ("GET", "/system/activity", get_activity_logs),
]
