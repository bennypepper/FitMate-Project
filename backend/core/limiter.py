import ipaddress
from starlette.requests import Request
from slowapi import Limiter

def get_client_ip(request: Request) -> str:
    """
    Extracts client IP address safely considering reverse proxies and CDNs.
    Evaluates CF-Connecting-IP, X-Forwarded-For, and X-Real-IP headers.
    Validates IP format to prevent spoofing or injection.
    Falls back to request.client.host or 127.0.0.1.
    """
    # 1. Cloudflare connecting IP
    cf_ip = request.headers.get("CF-Connecting-IP", "").strip()
    if cf_ip:
        try:
            ipaddress.ip_address(cf_ip)
            return cf_ip
        except ValueError:
            pass

    # 2. X-Forwarded-For: client, proxy1, proxy2
    xff = request.headers.get("X-Forwarded-For", "").strip()
    if xff:
        client_candidate = xff.split(",")[0].strip()
        try:
            ipaddress.ip_address(client_candidate)
            return client_candidate
        except ValueError:
            pass

    # 3. X-Real-IP
    x_real_ip = request.headers.get("X-Real-IP", "").strip()
    if x_real_ip:
        try:
            ipaddress.ip_address(x_real_ip)
            return x_real_ip
        except ValueError:
            pass

    # 4. Direct client connection host
    if request.client and request.client.host:
        return request.client.host

    return "127.0.0.1"

limiter = Limiter(key_func=get_client_ip)
