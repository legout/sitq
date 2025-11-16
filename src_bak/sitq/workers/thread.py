from __future__ import annotations
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

from .base import Worker


class ThreadWorker(Worker):
    """
    Worker that runs synchronous functions in a thread pool.

    The actual task function is executed synchronously in a worker thread by
    using a dedicated ThreadPoolExecutor. The coroutine only awaits the
    executor result so the function itself runs outside the event loop thread.
    """

    def __init__(self, *args, max_workers: Optional[int] = None, **kwargs):
        super().__init__(*args, **kwargs)
        self._executor = ThreadPoolExecutor(max_workers=max_workers)

    async def _execute(self, func, *args, context=None, **kwargs):
        loop = asyncio.get_running_loop()

        if context is None:
            return await loop.run_in_executor(self._executor, func, *args, **kwargs)

        # Wrap execution so it runs inside the captured context in the worker thread.
        def _runner():
            return context.run(func, *args, **kwargs)

        return await loop.run_in_executor(self._executor, _runner)

    async def stop(self):
        await super().stop()
        self._executor.shutdown(wait=True)
