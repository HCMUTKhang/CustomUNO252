"""Shared modules for Custom UNO Online."""

import socket


def get_local_ip() -> str:
    """Return the machine's LAN IP (the interface used to reach the outside world)."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"
