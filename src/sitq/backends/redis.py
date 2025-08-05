"""
Redis‑based backend – uses a list for immediate tasks, a sorted set for scheduled
tasks, and simple SETNX locks for atomic claiming.
"""

from __future__ import annotations
import asyncio
import json
import uuid
from datetime import datetime, timedelta
from typing import List, Optional

import aioredis
from ..core import Task, Result, _now
from .base import Backend


class RedisBackend(Backend):
    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        prefix: str = "pytaskqueue",
    ):
        self.host = host
        self.port = port
        self.db = db
        self.prefix = prefix.rstrip(":")
        self.redis: Optional[aioredis.Redis] = None

        # keys
        self.immediate_q = f"{self.prefix}:queue"
        self.scheduled_zset = f"{self.prefix}:scheduled"
        self.lock_prefix = f"{self.prefix}:lock"
        self.result_prefix = f"{self.prefix}:result"
        self.task_hash_prefix = f"{self.prefix}:task"

    # ------------------------------------------------------------------
    async def connect(self):
        self.redis = await aioredis.create_redis_pool(
            (self.host, self.port), db=self.db, encoding=None
        )

    async def close(self):
        if self.redis:
            self.redis.close()
            await self.redis.wait_closed()

    # ------------------------------------------------------------------
    async def enqueue(self, task: Task) -> None:
        """Store payload and push to immediate list or scheduled ZSET."""
        task_key = f"{self.task_hash_prefix}:{task.id}"
        await self.redis.hmset_dict(
            task_key,
            func=task.func,
            args=task.args or b"",
            kwargs=task.kwargs or b"",
            schedule=json.dumps(task.schedule) if task.schedule else "",
            created_at=task.created_at.isoformat(),
            next_run_time=task.next_run_time.isoformat() if task.next_run_time else "",
            retries=str(task.retries),
            max_retries=str(task.max_retries),
        )
        if task.next_run_time:
            score = task.next_run_time.timestamp()
            await self.redis.zadd(self.scheduled_zset, score, task.id)
        else:
            await self.redis.lpush(self.immediate_q, task.id)

    # ------------------------------------------------------------------
    async def fetch_due_tasks(self, limit: int = 1) -> List[Task]:
        """
        Return up to ``limit`` immediate tasks.
        A background coroutine (started by TaskQueue.start_scheduler) moves
        due scheduled tasks to the immediate list.
        """
        raw_ids = await self.redis.lrange(self.immediate_q, -limit, -1)
        tasks: List[Task] = []
        for raw in raw_ids:
            task_id = raw.decode()
            task = await self._load_task(task_id)
            if task:
                tasks.append(task)
        return tasks

    async def _load_task(self, task_id: str) -> Optional[Task]:
        task_key = f"{self.task_hash_prefix}:{task_id}"
        data = await self.redis.hgetall(task_key, encoding="utf-8")
        if not data:
            return None
        return Task(
            id=task_id,
            func=data["func"].encode(),
            args=data.get("args", "").encode(),
            kwargs=data.get("kwargs", "").encode(),
            schedule=json.loads(data["schedule"]) if data["schedule"] else None,
            created_at=datetime.fromisoformat(data["created_at"]),
            next_run_time=datetime.fromisoformat(data["next_run_time"])
            if data["next_run_time"]
            else None,
            retries=int(data.get("retries", "0")),
            max_retries=int(data.get("max_retries", "3")),
        )

    # ------------------------------------------------------------------
    async def update_task_state(self, task_id: str, **kwargs) -> None:
        task_key = f"{self.task_hash_prefix}:{task_id}"
        await self.redis.hmset_dict(task_key, **kwargs)

    # ------------------------------------------------------------------
    async def store_result(self, result: Result) -> None:
        result_key = f"{self.result_prefix}:{result.task_id}"
        await self.redis.hmset_dict(
            result_key,
            id=result.id,
            task_id=result.task_id,
            status=result.status,
            value=result.value or b"",
            traceback=result.traceback or "",
            retry_count=str(result.retry_count),
            last_retry_at=result.last_retry_at.isoformat()
            if result.last_retry_at
            else "",
        )

    async def get_result(self, task_id: str) -> Optional[Result]:
        result_key = f"{self.result_prefix}:{task_id}"
        data = await self.redis.hgetall(result_key, encoding="utf-8")
        if not data:
            return None
        return Result(
            id=data["id"],
            task_id=data["task_id"],
            status=data["status"],
            value=data["value"] if data["value"] else None,
            traceback=data["traceback"] if data["traceback"] else None,
            retry_count=int(data.get("retry_count", "0")),
            last_retry_at=datetime.fromisoformat(data["last_retry_at"])
            if data.get("last_retry_at")
            else None,
        )

    # ------------------------------------------------------------------
    async def claim_task(self, task_id: str, lock_timeout: int = 30) -> bool:
        lock_key = f"{self.lock_prefix}:{task_id}"
        result = await self.redis.set(
            lock_key, "1", expire=lock_timeout, exist=aioredis.commands.SET_IF_NOT_EXIST
        )
        return result is not None

    async def release_task(self, task_id: str) -> None:
        lock_key = f"{self.lock_prefix}:{task_id}"
        await self.redis.delete(lock_key)

    async def schedule_retry(self, task_id: str, delay: int) -> None:
        task_key = f"{self.task_hash_prefix}:{task_id}"
        await self.redis.hincrby(task_key, "retries", 1)
        next_time = _now() + timedelta(seconds=delay)
        await self.redis.hset(task_key, "next_run_time", next_time.isoformat())
        await self.redis.zadd(self.scheduled_zset, next_time.timestamp(), task_id)

    # ------------------------------------------------------------------
    # Background helper – moves due scheduled tasks to the immediate queue.
    # Called by ``TaskQueue.start_scheduler``.
    # ------------------------------------------------------------------
    async def _move_due_scheduled(self, poll_interval: float = 1.0) -> None:
        while True:
            now_ts = _now().timestamp()
            due = await self.redis.zrangebyscore(
                self.scheduled_zset, 0, now_ts, start=0, num=100, withscores=False
            )
            if due:
                await self.redis.zrem(self.scheduled_zset, *due)
                await self.redis.lpush(self.immediate_q, *due)
            await asyncio.sleep(poll_interval)
