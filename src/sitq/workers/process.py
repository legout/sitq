import asyncio
from concurrent.futures import ProcessPoolExecutor
from typing import Optional
import cloudpickle

from .base import Worker


def _run_in_process(serialized_ctx, serialized_func, args, kwargs):
    """
    Helper executed inside the worker process. It unpickles the context and
    function, restores the context (if provided), and executes the function.
    This keeps context propagation across process boundaries.
    """
    import cloudpickle as _cloudpickle

    ctx = None
    if serialized_ctx:
        try:
            ctx = _cloudpickle.loads(serialized_ctx)
        except Exception:
            ctx = None

    func = _cloudpickle.loads(serialized_func)

    if ctx:
        return ctx.run(func, *args, **kwargs)
    return func(*args, **kwargs)


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

    async def _execute(self, func, *args, context=None, **kwargs):
        loop = asyncio.get_running_loop()

        # Serialize function and context using cloudpickle so they can be
        # reconstructed inside the target process.
        serialized_func = cloudpickle.dumps(func)
        serialized_ctx = cloudpickle.dumps(context) if context is not None else None

        return await loop.run_in_executor(
            self._executor, _run_in_process, serialized_ctx, serialized_func, args, kwargs
        )

    async def stop(self):
        await super().stop()
        self._executor.shutdown(wait=True)
