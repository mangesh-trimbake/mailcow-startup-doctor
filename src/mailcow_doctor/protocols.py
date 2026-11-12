"""Network-level application readiness probes."""

import socket
from dataclasses import dataclass


def _recv_line(conn, max_bytes=4096):
    """Read one complete newline-terminated protocol line."""
    data = bytearray()

    while len(data) < max_bytes:
        chunk = conn.recv(min(1024, max_bytes - len(data)))

        if not chunk:
            break

        data.extend(chunk)

        if b"\n" in data:
            return bytes(data).split(b"\n", 1)[0] + b"\n"

    if not data:
        return b""

    raise OSError("Incomplete or oversized protocol response line")


@dataclass
class ProbeResult:
    name: str
    status: str
    detail: str
    elapsed_ms: float


def _recv_line(conn, max_bytes=4096):
    """Read one complete newline-terminated protocol line."""
    data = bytearray()

    while len(data) < max_bytes:
        chunk = conn.recv(min(1024, max_bytes - len(data)))

        if not chunk:
            break

        data.extend(chunk)

        if b"\n" in data:
            return bytes(data).split(b"\n", 1)[0] + b"\n"

    if not data:
        return b""

    raise OSError("Incomplete or oversized protocol response line")


def check_greeting(
    name: str,
    host: str,
    port: int,
    expected_prefix: bytes,
    timeout: float = 3.0,
) -> ProbeResult:
    """Connect to a TCP service and validate its initial protocol greeting."""
    import time

    start = time.monotonic()

    try:
        with socket.create_connection((host, port), timeout=timeout) as conn:
            conn.settimeout(timeout)
            greeting = _recv_line(conn)

        elapsed = (time.monotonic() - start) * 1000

        if not greeting:
            return ProbeResult(
                name, "FAIL", "Connection closed without a greeting", elapsed
            )

        first_line = greeting.splitlines()[0]

        if not first_line.startswith(expected_prefix):
            return ProbeResult(
                name,
                "FAIL",
                f"Unexpected greeting: {first_line.decode(errors='replace')}",
                elapsed,
            )

        return ProbeResult(
            name,
            "PASS",
            first_line.decode(errors="replace"),
            elapsed,
        )

    except (OSError, TimeoutError) as exc:
        elapsed = (time.monotonic() - start) * 1000
        return ProbeResult(name, "FAIL", str(exc), elapsed)


def check_smtp(host: str = "127.0.0.1", port: int = 25) -> ProbeResult:
    """Check the SMTP service greeting."""
    return check_greeting("Postfix SMTP", host, port, b"220")


def check_imap(host: str = "127.0.0.1", port: int = 143) -> ProbeResult:
    """Check the IMAP service greeting."""
    return check_greeting("Dovecot IMAP", host, port, b"* OK")


def check_mariadb(host: str = "127.0.0.1", port: int = 13306) -> ProbeResult:
    """Validate the initial MySQL/MariaDB protocol handshake."""
    import time

    start = time.monotonic()

    try:
        with socket.create_connection((host, port), timeout=3) as conn:
            conn.settimeout(3)

            header = conn.recv(4)
            if len(header) != 4:
                raise OSError("Incomplete MySQL handshake header")

            payload_length = int.from_bytes(header[:3], "little")
            if payload_length < 1 or payload_length > 65536:
                raise OSError("Invalid MySQL handshake packet length")

            payload = b""
            while len(payload) < payload_length:
                chunk = conn.recv(payload_length - len(payload))
                if not chunk:
                    raise OSError("Incomplete MySQL handshake packet")
                payload += chunk

        elapsed = (time.monotonic() - start) * 1000

        if payload[0] != 10:
            return ProbeResult(
                "MariaDB", "FAIL",
                f"Unexpected MySQL protocol version: {payload[0]}",
                elapsed,
            )

        return ProbeResult(
            "MariaDB", "PASS",
            "MySQL protocol handshake received",
            elapsed,
        )

    except (OSError, TimeoutError) as exc:
        elapsed = (time.monotonic() - start) * 1000
        return ProbeResult("MariaDB", "FAIL", str(exc), elapsed)


def check_redis(host: str = "127.0.0.1", port: int = 7654) -> ProbeResult:
    """Send a Redis PING command and inspect its response."""
    import time

    start = time.monotonic()

    try:
        with socket.create_connection((host, port), timeout=3) as conn:
            conn.settimeout(3)
            conn.sendall(b"*1\r\n$4\r\nPING\r\n")
            response = _recv_line(conn)

        elapsed = (time.monotonic() - start) * 1000

        if response.startswith(b"+PONG"):
            return ProbeResult(
                "Redis", "PASS", "PING returned PONG", elapsed
            )

        if response.startswith(b"-NOAUTH"):
            return ProbeResult(
                "Redis", "WARN",
                "Redis is reachable but requires authentication",
                elapsed,
            )

        return ProbeResult(
            "Redis", "FAIL",
            f"Unexpected response: {response.decode(errors='replace').strip()}",
            elapsed,
        )

    except (OSError, TimeoutError) as exc:
        elapsed = (time.monotonic() - start) * 1000
        return ProbeResult("Redis", "FAIL", str(exc), elapsed)
