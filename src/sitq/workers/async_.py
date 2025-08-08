from __future__ import annotations
import asyncio
from typing import Any, Callable
import concurrent.futures

from .base import Worker


class AsyncWorker(Worker):
    """
    Worker for native ``async`` callables.
    """

    async def _execute(self, func, *args, context=None, **kwargs):
        # Execute the function inside the provided context (if any). We create
        # the call inside the context so coroutine objects / coroutine functions
        # capture the intended context.
        def _call():
            return func(*args, **kwargs)

        if context is None:
            res = _call()
        else:
            res = context.run(_call)

        if asyncio.iscoroutine(res):
            return await res
        return res


def run_async_sync(func: Callable[..., Any], *args, **kwargs) -> Any:
    """
    Run an async callable from synchronous code, blocking until completion.

    - If there is no running event loop in the current thread, this uses
      ``asyncio.run``.
    - If an event loop is already running in the current thread (e.g. an
      interactive REPL), the coroutine will be executed on a new event loop
      running in a separate thread; this call will block until the coroutine
      completes and return its result.

    Notes:
    - `func` may be either an async function (callable) or an already-created
      coroutine object. If a regular (sync) callable is passed it will be
      executed directly and its return value returned.
    """
    # Prepare coroutine or value
    if asyncio.iscoroutinefunction(func):
        coro = func(*args, **kwargs)
    elif asyncio.iscoroutine(func):
        coro = func
    else:
        # Synchronous callable — just execute and return
        return func(*args, **kwargs)

    # If no running loop in this thread, use asyncio.run which manages a loop
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)

    # Running loop exists in this thread — run the coroutine in a new thread
    def _runner():
        loop = asyncio.new_event_loop()
        try:
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(coro)
        finally:
            try:
                loop.close()
            except Exception:
                pass

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
        future = ex.submit(_runner)
        return future.result()
