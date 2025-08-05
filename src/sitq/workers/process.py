import asyncio
from concurrent.futures import ProcessPoolExecutor
from typing import Optional

from .base import Worker


class ProcessWorker(Worker):
    """
    Worker that runs CPU‑bound functions in a separate process pool.
    """

    def __init__(
        self,
        *args,
        max_workers: Optional[int] = None,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self._executor = ProcessPoolExecutor(max_workers=max_workers)

    async def _execute(self, func, *args, **kwargs):
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(self._executor, func, *args, **kwargs)

    async def stop(self):
        await super().stop()
        self._executor.shutdown(wait=True)
