import marimo

__generated_with = "0.14.16"
app = marimo.App(width="medium")


@app.cell
def _():
    from sitq.task_queue2 import TaskQueue, Worker
    return TaskQueue, Worker


@app.cell
def _():
    # 1. Define your async task function
    async def say_hello(name: str):
        print(f"Hello, {name}")
        return f"Greetings, {name}!"

    def add(a, b):
        return a + b

    def long_running(name, seconds=5):
        import time
        time.sleep(seconds)
        return f"Hello, {name}!"
    return


@app.cell
def _(TaskQueue):
    q = TaskQueue("task_queue2.db")
    return (q,)


@app.cell
def _(q):
    task_id = q.enqueue("add", args=(2, 3))

    # Enqueue with a future run time (e.g. 2 minutes from now)
    from datetime import datetime, timedelta
    task_id2 = q.enqueue(
        "long_running",
        kwargs={"name": "Bob"},
        run_at=datetime.utcnow() + timedelta(minutes=2),
        serialize="pickle",            # optional (json is default)
    )
    return (task_id,)


@app.cell
def _(Worker):
    worker = Worker("task_queue2.db")
    worker.run_forever(poll_interval=1.0)
    return


@app.cell
def _(q, task_id):
    status, result = q.get_status(task_id)
    return (result,)


@app.cell
def _(result):
    result
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
