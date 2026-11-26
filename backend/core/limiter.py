import ipaddress

from core.config import settings
from slowapi import Limiter
from starlette.requests import Request

_LOOPBACK_NETWORKS = (
    ipaddress.ip_network("127.0.0.1/32"),
    ipaddress.ip_network("::1/128"),
)


def _get_trusted_proxy_networks() -> list[ipaddress.IPv4Network | ipaddress.IPv6Network]:
    """Parse configured TRUSTED_PROXIES (comma-separated IPs/CIDRs) plus loopback."""
    networks: list[ipaddress.IPv4Network | ipaddress.IPv6Network] = list(_LOOPBACK_NETWORKS)
    raw = (settings.TRUSTED_PROXIES or "").strip()
    if not raw:
        return networks
    for entry in raw.split(","):
        token = entry.strip()
        if not token:
            continue
        try:
            networks.append(ipaddress.ip_network(token, strict=False))
        except ValueError:
            continue
    return networks


def _is_ip_in_networks(
    ip_str: str,
    networks: list[ipaddress.IPv4Network | ipaddress.IPv6Network],
) -> bool:
    try:
        addr = ipaddress.ip_address(ip_str)
    except ValueError:
        return False
    return any(addr in net for net in networks)


def _parse_valid_ip(candidate: str) -> str | None:
    cleaned = candidate.strip()
    if not cleaned:
        return None
    try:
        ipaddress.ip_address(cleaned)
        return cleaned
    except ValueError:
        return None


def get_client_ip(request: Request) -> str:
    """
    Extracts client IP address safely considering trusted reverse proxies and CDNs.
    Only trusts CF-Connecting-IP, X-Forwarded-For, and X-Real-IP when the direct
    peer (request.client.host) belongs to the trusted proxy allowlist.
    For X-Forwarded-For, selects the rightmost non-trusted IP.
    """
    client_host = (request.client.host if request.client and request.client.host else "").strip()
    if not client_host:
        return "127.0.0.1"

    trusted_networks = _get_trusted_proxy_networks()
    if not _is_ip_in_networks(client_host, trusted_networks):
        return client_host

    # 1. Cloudflare connecting IP
    cf_ip = _parse_valid_ip(request.headers.get("CF-Connecting-IP", ""))
    if cf_ip:
        return cf_ip

    # 2. X-Forwarded-For: pick rightmost non-trusted IP
    xff = request.headers.get("X-Forwarded-For", "").strip()
    if xff:
        valid_ips = [ip for part in xff.split(",") if (ip := _parse_valid_ip(part))]
        for candidate in reversed(valid_ips):
            if not _is_ip_in_networks(candidate, trusted_networks):
                return candidate
        if valid_ips:
            return valid_ips[0]

    # 3. X-Real-IP
    x_real_ip = _parse_valid_ip(request.headers.get("X-Real-IP", ""))
    if x_real_ip:
        return x_real_ip

    return client_host


limiter = Limiter(key_func=get_client_ip)
