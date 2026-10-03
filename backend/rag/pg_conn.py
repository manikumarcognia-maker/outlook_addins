"""Postgres connection helpers — prefer IPv4 to avoid slow/broken IPv6 multi-connect attempts."""

from __future__ import annotations

import logging
import socket
from functools import lru_cache

from psycopg.conninfo import conninfo_to_dict, make_conninfo

logger = logging.getLogger("fr8labs.pgconn")

CONNECT_TIMEOUT_SEC = 20
POOL_WAIT_TIMEOUT_SEC = 45


@lru_cache(maxsize=8)
def resolve_ipv4(host: str) -> str | None:
    try:
        infos = socket.getaddrinfo(host, 5432, socket.AF_INET, socket.SOCK_STREAM)
    except OSError as exc:
        logger.warning("PG_DNS_FAILED | host=%s | error=%s", host, exc)
        return None
    if not infos:
        return None
    return infos[0][4][0]


def clear_dns_cache() -> None:
    resolve_ipv4.cache_clear()


def build_database_conninfo(database_url: str, *, prefer_ipv4: bool = True) -> str:
    params = conninfo_to_dict(database_url)
    host = params.get("host")
    if prefer_ipv4 and host:
        hostaddr = resolve_ipv4(host)
        if hostaddr:
            params["hostaddr"] = hostaddr
            logger.info("PG_CONNINFO | host=%s hostaddr=%s (IPv4 only)", host, hostaddr)
        else:
            logger.warning("PG_CONNINFO | host=%s | no IPv4; using default libpq resolve", host)
    return make_conninfo(**params)


def connection_kwargs() -> dict:
    return {"connect_timeout": CONNECT_TIMEOUT_SEC}
