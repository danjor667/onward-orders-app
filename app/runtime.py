"""Where this container is running: used to show which task and zone
answered a request, which makes load balancing and blue/green visible."""
import json
import os
import socket
import urllib.request
from functools import lru_cache


@lru_cache(maxsize=1)
def describe() -> dict:
    info = {"task": socket.gethostname(), "zone": "local"}
    # ECS provides this link-local address inside every task. It is not an
    # internet call.
    metadata_url = os.environ.get("ECS_CONTAINER_METADATA_URI_V4")
    if not metadata_url:
        return info
    try:
        with urllib.request.urlopen(f"{metadata_url}/task", timeout=2) as response:
            task = json.load(response)
        info["task"] = task["TaskARN"].rsplit("/", 1)[-1][:8]
        info["zone"] = task.get("AvailabilityZone", "unknown")
    except (OSError, KeyError, ValueError):
        pass
    return info
