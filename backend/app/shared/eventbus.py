"""In-memory async event bus for pipeline streaming (SSE)."""

import asyncio
import json
from collections import deque
from datetime import datetime, timezone
from itertools import count

_subscribers: set[asyncio.Queue] = set()
_history: deque = deque(maxlen=500)
_ids = count(1)


def publish(t: str, msg: str, level: str = "info", **extra) -> None:
    """Publish narasi event. Aman dipanggil dari kode sinkron/async."""
    event = {
        "id": next(_ids),
        "t": t,
        "level": level,
        "msg": msg,
        "ts": datetime.now(timezone.utc).isoformat(),
        **extra,
    }
    _history.append(event)
    data = json.dumps(event, ensure_ascii=False, default=str)
    for q in list(_subscribers):
        try:
            q.put_nowait(data)
        except asyncio.QueueFull:
            pass


async def subscribe() -> asyncio.Queue:
    q: asyncio.Queue = asyncio.Queue(maxsize=200)
    _subscribers.add(q)
    return q


def unsubscribe(q: asyncio.Queue) -> None:
    _subscribers.discard(q)


def history(limit: int = 100) -> list[dict]:
    return list(_history)[-limit:]
