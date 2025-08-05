from .base import Worker


class AsyncWorker(Worker):
    """
    Worker for native ``async`` callables.
    """

    async def _execute(self, func, *args, **kwargs):
        return await func(*args, **kwargs)
