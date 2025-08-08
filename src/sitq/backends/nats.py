"""
NATS (JetStream) backend – uses a stream for persistence and a queue group for
load‑balancing across workers.
"""

from __future__ import annotations

import json
import uuid
import base64
from datetime import datetime, timedelta
from typing import List, Optional

from nats.aio.client import Client as NATS
from nats.js.api import StreamConfig, ConsumerConfig, RetentionPolicy
from nats.js.errors import NotFoundError

from ..core import Task, Result, _now
from .base import Backend


class NatsBackend(Backend):
    def __init__(
        self,
        servers: List[str] = ["nats://localhost:4222"],
        stream: str = "tasks",
        queue_group: str = "workers",
    ):
        self.servers = servers
        self.stream_name = stream
        self.queue_group = queue_group

        self.nc: Optional[NATS] = None
        self.js = None

        self.task_subject = f"{self.stream_name}.immediate"
        self.schedule_subject = f"{self.stream_name}.scheduled"
        self.result_subject = f"{self.stream_name}.results"

    # ------------------------------------------------------------------
    async def connect(self):
        self.nc = NATS()
        await self.nc.connect(servers=self.servers)
        self.js = self.nc.jetstream()

        cfg = StreamConfig(
            name=self.stream_name,
            subjects=[
                self.task_subject,
                self.schedule_subject,
                self.result_subject,
            ],
            retention=RetentionPolicy.Limits,
            max_msgs=1_000_000,
        )
        try:
            await self.js.add_stream(cfg)
        except Exception:
            # Stream already exists – ignore.
            pass

    async def close(self):
        if self.nc:
            await self.nc.close()

    # ------------------------------------------------------------------
    async def enqueue(self, task: Task) -> None:
        """
        Store the task payload in a KV bucket (named ``tasks``) and publish a
        reference message on either the immediate or scheduled subject.
        """
        kv = await self.js.key_value(bucket="tasks")

        def _b64_or_none(b: Optional[bytes]) -> Optional[str]:
            if b is None or b == b"":
                return None
            return base64.b64encode(b).decode("ascii")

        payload = {
            "id": task.id,
            # Store binary-safe base64 strings for func/args/kwargs/context
            "func": _b64_or_none(task.func),
            "args": _b64_or_none(task.args),
            "kwargs": _b64_or_none(task.kwargs),
            "context": _b64_or_none(task.context),
            "schedule": task.schedule,
            "created_at": task.created_at.isoformat(),
            "next_run_time": task.next_run_time.isoformat()
            if task.next_run_time
            else None,
            "retries": task.retries,
            "max_retries": task.max_retries,
        }
        await kv.put(task.id, json.dumps(payload).encode())

        subject = self.task_subject if not task.next_run_time else self.schedule_subject
        await self.js.publish(subject, json.dumps(payload).encode())

    # ------------------------------------------------------------------
    async def fetch_due_tasks(self, limit: int = 1) -> List[Task]:
        """
        Pull from the *immediate* subject using a queue group.
        Queue groups guarantee exclusive delivery to a single consumer.
        """
        sub = await self.js.pull_subscribe(
            self.task_subject,
            queue=self.queue_group,
            config=ConsumerConfig(
                ack_wait=30_000_000_000,  # 30 s
                deliver_policy="all",
                max_deliver=1,
                max_ack_pending=limit,
            ),
        )
        msgs = await sub.fetch(limit, timeout=1_000_000_000)  # 1 s
        tasks: List[Task] = []

        def _maybe_b64_decode(s: Optional[str]) -> Optional[bytes]:
            if s is None:
                return None
            try:
                return base64.b64decode(s.encode("ascii"))
            except Exception:
                # Fallback: return raw utf-8 bytes
                return s.encode("utf-8")

        for msg in msgs:
            data = json.loads(msg.data.decode())
            tasks.append(
                Task(
                    id=data["id"],
                    func=_maybe_b64_decode(data.get("func")),
                    args=_maybe_b64_decode(data.get("args")),
                    kwargs=_maybe_b64_decode(data.get("kwargs")),
                    context=_maybe_b64_decode(data.get("context")),
                    schedule=data.get("schedule"),
                    created_at=datetime.fromisoformat(data["created_at"]),
                    next_run_time=datetime.fromisoformat(data["next_run_time"])
                    if data.get("next_run_time")
                    else None,
                    retries=data.get("retries", 0),
                    max_retries=data.get("max_retries", 3),
                )
            )
            await msg.ack()
        return tasks

    # ------------------------------------------------------------------
    async def update_task_state(self, task_id: str, **kwargs) -> None:
        kv = await self.js.key_value(bucket="tasks")
        entry = await kv.get(task_id)
        data = json.loads(entry.value.decode())

        # If kwargs contains bytes (e.g., result_id as bytes), ensure they are str
        def _maybe_b64_bytes(v):
            if isinstance(v, (bytes, bytearray)):
                return base64.b64encode(bytes(v)).decode("ascii")
            return v

        for k, v in kwargs.items():
            data[k] = _maybe_b64_bytes(v)

        await kv.put(task_id, json.dumps(data).encode())

    # ------------------------------------------------------------------
    async def store_result(self, result: Result) -> None:
        def _b64_or_none(b: Optional[bytes]) -> Optional[str]:
            if b is None or b == b"":
                return None
            return base64.b64encode(b).decode("ascii")

        await self.js.publish(
            self.result_subject,
            json.dumps(
                {
                    "task_id": result.task_id,
                    "status": result.status,
                    "value": _b64_or_none(result.value),
                    "traceback": result.traceback,
                    "retry_count": result.retry_count,
                    "last_retry_at": result.last_retry_at.isoformat()
                    if result.last_retry_at
                    else None,
                }
            ).encode(),
        )

    async def get_result(self, task_id: str) -> Optional[Result]:
        """
        Pull a single result message that matches ``task_id``.
        We use a temporary pull subscription; the broker holds the message until
        it is ack‑ed.
        """
        try:
            sub = await self.js.pull_subscribe(
                self.result_subject,
                durable=f"result_{task_id}",
                config=ConsumerConfig(
                    filter_subject=self.result_subject, ack_wait=30_000_000_000
                ),
            )
            msgs = await sub.fetch(1, timeout=5_000_000_000)  # 5 s
            for msg in msgs:
                payload = json.loads(msg.data.decode())
                if payload["task_id"] == task_id:
                    await msg.ack()

                    def _maybe_b64_decode(s: Optional[str]) -> Optional[bytes]:
                        if s is None:
                            return None
                        try:
                            return base64.b64decode(s.encode("ascii"))
                        except Exception:
                            return s.encode("utf-8")

                    return Result(
                        id=str(uuid.uuid4()),
                        task_id=task_id,
                        status=payload["status"],
                        value=_maybe_b64_decode(payload.get("value")),
                        traceback=payload.get("traceback"),
                        retry_count=int(payload.get("retry_count", 0)),
                        last_retry_at=datetime.fromisoformat(payload["last_retry_at"])
                        if payload.get("last_retry_at")
                        else None,
                    )
        except NotFoundError:
            return None
        return None

    # ------------------------------------------------------------------
    async def claim_task(self, task_id: str, lock_timeout: int = 30) -> bool:
        """
        JetStream queue groups already guarantee exclusive delivery, so we simply
        return ``True`` for API compatibility.
        """
        return True

    async def release_task(self, task_id: str) -> None:
        # No explicit release needed; JetStream's ack‑wait timeout releases the claim.
        return None

    async def schedule_retry(self, task_id: str, delay: int) -> None:
        """
        Increment retry counter in KV and republish on the *scheduled* subject.
        """
        kv = await self.js.key_value(bucket="tasks")
        entry = await kv.get(task_id)
        data = json.loads(entry.value.decode())
        data["retries"] = data.get("retries", 0) + 1
        next_time = _now() + timedelta(seconds=delay)
        data["next_run_time"] = next_time.isoformat()
        await kv.put(task_id, json.dumps(data).encode())
        await self.js.publish(self.schedule_subject, json.dumps(data).encode())
