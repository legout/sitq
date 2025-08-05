import asyncio
from .base import Worker


class ThreadWorker(Worker):
    """
    Worker that runs synchronous functions in a thread pool via ``asyncio.to_thread``.
    """

    async def _execute(self, func, *args, **kwargs):
        return await asyncio.to_thread(func, *args, **kwargs)
