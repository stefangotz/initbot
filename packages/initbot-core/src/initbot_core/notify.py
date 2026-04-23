# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""UDP-based change notification for state consumers.

Design (Plan A — single consumer):
    After any character or player write, the writer sends a zero-byte UDP datagram
    to a configured host:port. The web app listens on that port and wakes its SSE
    connections immediately, rather than waiting for the next poll cycle.

    Single-consumer limitation: each sender must know every recipient's address.
    Scaling the web app to N instances requires N send_notification() calls per
    write, one per instance — the sender must be aware of every sink.

Plan B alternative (M:N fan-out without sender awareness):
    Replace send_notification() with path.touch() on a flag file that lives on a
    shared named Docker volume backed by tmpfs:

        volumes:
          notify:
            driver: local
            driver_opts:
              type: tmpfs
              device: tmpfs
              o: size=1m

    Each web app instance watches the flag file with watchfiles.awatch(). The OS
    kernel (inotify on Linux) fans the notification out to all watchers
    independently — sinks can be added or removed without any change to the
    senders. The tmpfs volume requires no disk I/O and is transient by nature.
"""

import logging
import socket

_log = logging.getLogger(__name__)


def send_notification(host: str, port: int) -> None:
    """Send a zero-byte UDP datagram to notify a change consumer.

    Fire-and-forget: errors are logged at DEBUG level and silently swallowed,
    so a missing or not-yet-started consumer never blocks a write.
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.sendto(b"", (host, port))
    except OSError as exc:
        _log.debug("Notification send to %s:%d failed: %s", host, port, exc)
