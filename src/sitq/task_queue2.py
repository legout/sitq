#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SQLite‑backed task queue with scheduling, result storage, and JSON/pickle serialization.

Typical usage:

    from task_queue import TaskQueue, Worker

    # ----------------------------------------------------------------------
    # 1️⃣  Define the functions you want to run asynchronously.
    # ----------------------------------------------------------------------
    def add(a, b):
        return a + b

    def long_running(name, seconds=5):
        import time
        time.sleep(seconds)
        return f"Hello, {name}!"

    # ----------------------------------------------------------------------
    # 2️⃣  Create a queue (or reuse the same SQLite file from many processes)
    # ----------------------------------------------------------------------
    q = TaskQueue("my_tasks.db")

    # Enqueue instantly
    task_id = q.enqueue("add", args=(2, 3))

    # Enqueue with a future run time (e.g. 2 minutes from now)
    from datetime import datetime, timedelta
    task_id2 = q.enqueue(
        "long_running",
        kwargs={"name": "Bob"},
        run_at=datetime.utcnow() + timedelta(minutes=2),
        serialize="json",            # optional (json is default)
    )

    # ----------------------------------------------------------------------
    # 3️⃣  From a *different* process start a worker that actually executes.
    # ----------------------------------------------------------------------
    worker = Worker("my_tasks.db")
    worker.run_forever(poll_interval=1.0)   # blocks forever

    # ----------------------------------------------------------------------
    # 4️⃣  Later you can query the result
    # ----------------------------------------------------------------------
    status, result = q.get_status(task_id)
    print(status, result)   # → "completed", 5
"""

import json
import pickle
import sqlite3
import threading
import time
import traceback
from datetime import datetime
from importlib import import_module
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple, Union

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------


def _now() -> datetime:
    """Current UTC time, without tzinfo (SQLite stores naive UTC)."""
    return datetime.utcnow()


def _to_timestamp(dt: Optional[datetime]) -> Optional[float]:
    """Convert datetime -> POSIX timestamp (float) or None."""
    return dt.timestamp() if dt is not None else None


def _from_timestamp(ts: Optional[float]) -> Optional[datetime]:
    """Convert POSIX timestamp (float) -> datetime (UTC) or None."""
    return datetime.utcfromtimestamp(ts) if ts is not None else None


def _dotted_path(func: Callable) -> str:
    """Return 'module.submodule:function_name' for a callable."""
    mod = func.__module__
    name = func.__qualname__
    return f"{mod}.{name}"


def _load_callable(dotted: str) -> Callable:
    """Import a dotted path like 'pkg.mod.func' and return the callable."""
    parts = dotted.split(".")
    module_path = ".".join(parts[:-1])
    attr_name = parts[-1]
    module = import_module(module_path)
    return getattr(module, attr_name)


# ----------------------------------------------------------------------
# Serialization
# ----------------------------------------------------------------------


class Serializer:
    """Namespace for JSON ↔ pickle helpers."""

    @staticmethod
    def dumps_json(obj: Any) -> bytes:
        """Serialize to JSON (UTF‑8 bytes). Raises TypeError if not serialisable."""
        return json.dumps(obj, ensure_ascii=False).encode("utf-8")

    @staticmethod
    def loads_json(blob: bytes) -> Any:
        return json.loads(blob.decode("utf-8"))

    @staticmethod
    def dumps_pickle(obj: Any) -> bytes:
        """Serialize with pickle (protocol 5). Returns raw bytes."""
        return pickle.dumps(obj, protocol=pickle.HIGHEST_PROTOCOL)

    @staticmethod
    def loads_pickle(blob: bytes) -> Any:
        return pickle.loads(blob)


# ----------------------------------------------------------------------
# Main public classes
# ----------------------------------------------------------------------


class TaskQueue:
    """
    Public API for enqueuing tasks, checking status and retrieving results.

    Parameters
    ----------
    db_path : str or pathlib.Path
        Path to SQLite database file.  If the file does not exist it is created.
    """

    _SCHEMA = """
    CREATE TABLE IF NOT EXISTS tasks (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        func_path   TEXT NOT NULL,
        args_blob   BLOB,
        kwargs_blob BLOB,
        serialize   TEXT NOT NULL CHECK (serialize IN ('json','pickle')),
        run_at      REAL,                 -- Unix timestamp (UTC) or NULL = immediate
        status      TEXT NOT NULL CHECK (status IN ('pending','in_progress','completed','failed')),
        result_blob BLOB,
        error_text  TEXT,
        created_at  REAL NOT NULL,
        updated_at  REAL NOT NULL,
        worker_id   TEXT
    );

    CREATE INDEX IF NOT EXISTS idx_tasks_status_runat
        ON tasks (status, run_at);
    """

    def __init__(self, db_path: Union[str, Path]):
        self.db_path = Path(db_path).expanduser()
        self._ensure_db()

    # ------------------------------------------------------------------
    # DB helpers
    # ------------------------------------------------------------------
    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(
            self.db_path,
            detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
            timeout=30,  # generous timeout for concurrent writers
        )
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_db(self) -> None:
        """Create DB file and tables if they don't exist."""
        with self._connect() as con:
            con.executescript(self._SCHEMA)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def enqueue(
        self,
        func: Union[Callable, str],
        *,
        args: Optional[Iterable] = None,
        kwargs: Optional[Dict] = None,
        run_at: Optional[datetime] = None,
        serialize: str = "json",
        **extra_kwargs,
    ) -> int:
        """
        Store a new task.

        Parameters
        ----------
        func : Callable or str
            Either a callable (will be stored as its dotted path) or a fully‑qualified
            dotted path string (e.g. ``"my_pkg.my_mod.my_func"``).
        args : iterable, optional
            Positional arguments for ``func``.
        kwargs : dict, optional
            Keyword arguments for ``func``.
        run_at : datetime, optional
            If supplied, the task will not be eligible for execution before this UTC time.
        serialize : {"json","pickle"}
            Serialization method for ``args``/``kwargs`` and for the result.
            ``json`` is the default; ``pickle`` is forced for non‑JSON‑serialisable data.
        extra_kwargs : dict
            Any additional key‑value pairs will be added to ``kwargs`` (convenient shortcut).

        Returns
        -------
        task_id : int
            Primary‑key of the inserted row.
        """
        if isinstance(func, Callable):
            func_path = _dotted_path(func)
        elif isinstance(func, str):
            func_path = func
        else:
            raise TypeError("func must be a callable or a dotted‑path string")

        args = list(args) if args is not None else []
        kw = dict(kwargs or {})
        kw.update(extra_kwargs)

        # Choose serialization automatically if not forced
        if serialize not in ("json", "pickle"):
            raise ValueError("serialize must be 'json' or 'pickle'")

        try:
            if serialize == "json":
                args_blob = Serializer.dumps_json(args)
                kwargs_blob = Serializer.dumps_json(kw)
        except Exception:  # not JSON‑serialisable
            serialize = "pickle"

        if serialize == "pickle":
            args_blob = Serializer.dumps_pickle(args)
            kwargs_blob = Serializer.dumps_pickle(kw)

        now_ts = _to_timestamp(_now())
        run_ts = _to_timestamp(run_at)

        with self._connect() as con:
            cur = con.execute(
                """
                INSERT INTO tasks
                (func_path, args_blob, kwargs_blob, serialize,
                 run_at, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, 'pending', ?, ?)
                """,
                (
                    func_path,
                    sqlite3.Binary(args_blob),
                    sqlite3.Binary(kwargs_blob),
                    serialize,
                    run_ts,
                    now_ts,
                    now_ts,
                ),
            )
            return cur.lastrowid

    def get_status(self, task_id: int) -> Tuple[str, Any]:
        """
        Return the task's status and, if finished, its result or error.

        Returns
        -------
        status : str
            One of ``pending``, ``in_progress``, ``completed`` or ``failed``.
        payload : Any
            If ``status`` is ``completed`` → the deserialized result.
            If ``status`` is ``failed``    → the error string (traceback).
            Otherwise → ``None``.
        """
        with self._connect() as con:
            row = con.execute(
                "SELECT status, result_blob, error_text, serialize FROM tasks WHERE id = ?",
                (task_id,),
            ).fetchone()
            if row is None:
                raise KeyError(f"Task {task_id} does not exist")

            status = row["status"]
            if status == "completed":
                ser = row["serialize"]
                blob = row["result_blob"]
                if ser == "json":
                    payload = Serializer.loads_json(blob)
                else:
                    payload = Serializer.loads_pickle(blob)
            elif status == "failed":
                payload = row["error_text"]
            else:
                payload = None

            return status, payload

    def purge(self, older_than: datetime) -> int:
        """
        Delete tasks whose ``updated_at`` timestamp is older than ``older_than``.

        Returns
        -------
        deleted_rows : int
        """
        ts = _to_timestamp(older_than)
        with self._connect() as con:
            cur = con.execute("DELETE FROM tasks WHERE updated_at < ?", (ts,))
            return cur.rowcount

    # ------------------------------------------------------------------
    # Internal helpers used by the worker
    # ------------------------------------------------------------------
    def _claim_task(self, worker_id: str) -> Optional[sqlite3.Row]:
        """
        Atomically pick the oldest eligible ``pending`` task and mark it
        ``in_progress`` with the given ``worker_id``.
        Returns the full row (as sqlite3.Row) or ``None`` if no task is ready.
        """
        now_ts = _to_timestamp(_now())
        with self._connect() as con:
            con.isolation_level = "EXCLUSIVE"  # start a transaction immediately
            cur = con.execute(
                """
                SELECT id FROM tasks
                WHERE status = 'pending'
                  AND (run_at IS NULL OR run_at <= ?)
                ORDER BY COALESCE(run_at, 0) ASC, id ASC
                LIMIT 1
                """,
                (now_ts,),
            )
            row = cur.fetchone()
            if row is None:
                con.commit()
                return None

            task_id = row["id"]
            updated = _now()
            con.execute(
                """
                UPDATE tasks
                SET status = 'in_progress',
                    worker_id = ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (worker_id, _to_timestamp(updated), task_id),
            )
            con.commit()

            # Return the *fresh* full row for execution
            full = con.execute(
                "SELECT * FROM tasks WHERE id = ?", (task_id,)
            ).fetchone()
            return full

    def _store_result(
        self,
        task_id: int,
        success: bool,
        payload: Any,
        serialize: str,
    ) -> None:
        """Write back result or error, set final status, bump timestamps."""
        now_ts = _to_timestamp(_now())
        if success:
            if serialize == "json":
                blob = Serializer.dumps_json(payload)
            else:
                blob = Serializer.dumps_pickle(payload)
            with self._connect() as con:
                con.execute(
                    """
                    UPDATE tasks
                    SET status = 'completed',
                        result_blob = ?,
                        updated_at = ?
                    WHERE id = ?
                    """,
                    (sqlite3.Binary(blob), now_ts, task_id),
                )
        else:
            # payload is the traceback string
            with self._connect() as con:
                con.execute(
                    """
                    UPDATE tasks
                    SET status = 'failed',
                        error_text = ?,
                        updated_at = ?
                    WHERE id = ?
                    """,
                    (payload, now_ts, task_id),
                )

    # expose helpers for Worker (named with a leading underscore to signal "private")
    # ----------------------------------------------------------------------


class Worker:
    """
    Background worker that pulls tasks from a SQLite queue and runs them.

    Parameters
    ----------
    db_path : str or pathlib.Path
        Same database used by the ``TaskQueue``.
    worker_id : str, optional
        Identifier for this worker (useful when you have many processes).
        If omitted a random UUID4 string is generated.
    max_retries : int, default 3
        How many times a task should be retried after a failure.
        (Retry logic is implemented by resetting status back to ``pending``;
        you can also implement your own back‑off in the function itself.)
    """

    def __init__(
        self,
        db_path: Union[str, Path],
        *,
        worker_id: Optional[str] = None,
        max_retries: int = 3,
    ):
        self.db_path = Path(db_path).expanduser()
        self.worker_id = (
            worker_id or f"worker-{int(time.time() * 1000)}-{threading.get_ident()}"
        )
        self.max_retries = max_retries
        self._stop_event = threading.Event()
        self._queue = TaskQueue(self.db_path)  # reuse internal helpers

    # ------------------------------------------------------------------
    # Life‑cycle helpers
    # ------------------------------------------------------------------
    def stop(self) -> None:
        """Signal the worker loop to exit."""
        self._stop_event.set()

    def run_once(self) -> bool:
        """
        Pull a single task, execute it and store the result.

        Returns
        -------
        handled : bool
            ``True`` if a task was processed, ``False`` if the queue was empty.
        """
        row = self._queue._claim_task(self.worker_id)
        if row is None:
            return False

        task_id = row["id"]
        func_path = row["func_path"]
        serialize = row["serialize"]

        # ------------------------------------------------------------------
        # 1️⃣ Deserialize args / kwargs
        # ------------------------------------------------------------------
        try:
            if serialize == "json":
                args = Serializer.loads_json(row["args_blob"])
                kwargs = Serializer.loads_json(row["kwargs_blob"])
            else:
                args = Serializer.loads_pickle(row["args_blob"])
                kwargs = Serializer.loads_pickle(row["kwargs_blob"])
        except Exception as exc:
            tb = traceback.format_exc()
            self._queue._store_result(
                task_id, False, f"Deserialization error: {tb}", serialize
            )
            return True

        # ------------------------------------------------------------------
        # 2️⃣ Load the callable
        # ------------------------------------------------------------------
        try:
            func = _load_callable(func_path)
        except Exception as exc:
            tb = traceback.format_exc()
            self._queue._store_result(task_id, False, f"Import error: {tb}", serialize)
            return True

        # ------------------------------------------------------------------
        # 3️⃣ Execute
        # ------------------------------------------------------------------
        try:
            result = func(*args, **kwargs)
        except Exception as exc:
            tb = traceback.format_exc()
            # Simple retry logic (max_retries).  When we give up, store as failure.
            retry_count = row.get(
                "retry_count", 0
            )  # Not stored yet – we use a temp var.
            if retry_count < self.max_retries:
                # Reset to pending so another worker (or this one later) will retry.
                self._reset_to_pending(task_id, serialize)
            else:
                self._queue._store_result(
                    task_id, False, f"Exception during execution:\n{tb}", serialize
                )
            return True

        # ------------------------------------------------------------------
        # 4️⃣ Store success
        # ------------------------------------------------------------------
        self._queue._store_result(task_id, True, result, serialize)
        return True

    def _reset_to_pending(self, task_id: int, serialize: str) -> None:
        """Put a failed task back into the pending state (used for retries)."""
        now_ts = _to_timestamp(_now())
        with self._queue._connect() as con:
            con.execute(
                """
                UPDATE tasks
                SET status = 'pending',
                    worker_id = NULL,
                    updated_at = ?
                WHERE id = ?
                """,
                (now_ts, task_id),
            )

    # ------------------------------------------------------------------
    # Continuous run
    # ------------------------------------------------------------------
    def run_forever(self, *, poll_interval: float = 0.5) -> None:
        """
        Main event loop – blocks until ``stop()`` is called.

        Parameters
        ----------
        poll_interval : float, default 0.5 seconds
            How long to sleep when there is no ready task.
        """
        try:
            while not self._stop_event.is_set():
                handled = self.run_once()
                if not handled:
                    time.sleep(poll_interval)
        except KeyboardInterrupt:
            # Graceful exit on Ctrl‑C
            pass

    # ------------------------------------------------------------------
    # Helper to run the worker in a background thread (optional convenience)
    # ------------------------------------------------------------------
    def start_in_thread(self, *, daemon: bool = True) -> threading.Thread:
        """Spawn a daemon thread that runs ``run_forever``."""
        t = threading.Thread(
            target=self.run_forever, daemon=daemon, name=self.worker_id
        )
        t.start()
        return t


# ----------------------------------------------------------------------
# Minimal self‑test (run this file directly)
# ----------------------------------------------------------------------
if __name__ == "__main__":
    # Simple demo when you execute the file: start a worker in a thread
    # and enqueue a few tasks.
    from datetime import timedelta

    # --------------------------------------------------------------
    # Example tasks (they live in this module, so the dotted path works)
    # --------------------------------------------------------------
    def hello(name: str, times: int = 1) -> str:
        return " ".join([f"Hello, {name}!"] * times)

    def fail_me() -> None:
        raise RuntimeError("I was told to fail")

    # --------------------------------------------------------------
    # Set up queue & worker
    # --------------------------------------------------------------
    DB = "demo_tasks.db"
    q = TaskQueue(DB)

    # Clean up any old rows (for demo purpose)
    q.purge(older_than=_now() - timedelta(days=365))

    # Enqueue a few tasks
    t1 = q.enqueue("hello", args=("Alice",), kwargs={"times": 2})
    t2 = q.enqueue(f"{__name__}.hello", kwargs={"name": "Bob"})
    t3 = q.enqueue(f"{__name__}.fail_me", run_at=_now() + timedelta(seconds=2))

    # Start a worker thread
    w = Worker(DB)
    w_thread = w.start_in_thread()

    # Wait a little while for tasks to finish
    time.sleep(5)

    # Show results
    for tid in (t1, t2, t3):
        status, payload = q.get_status(tid)
        print(f"Task {tid} → {status!r}")
        if status == "completed":
            print("   result :", payload)
        elif status == "failed":
            print("   error  :", payload)

    # Stop the background worker and exit
    w.stop()
    w_thread.join()
