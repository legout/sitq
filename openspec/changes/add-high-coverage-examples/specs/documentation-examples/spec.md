# documentation-examples Specification

## MODIFIED Requirements

### Requirement: Basic Examples Organization
The documentation SHALL provide a minimal, curated set of runnable examples under `examples/basic/` that covers the main v1 sitq features.

#### Scenario: User finds runnable examples
- **WHEN** a user navigates to the repository’s `examples/` directory or the documentation’s examples section
- **THEN** they SHALL find a short list of runnable scripts under `examples/basic/`
- **AND** each script SHALL state (in a header comment) the primary feature it demonstrates

### Requirement: Simple Task Processing Example
The documentation SHALL provide a first example that demonstrates the full v1 execution loop: enqueue a task, run a worker, and retrieve and deserialize the result.

#### Scenario: User achieves first success
- **WHEN** a new user runs `examples/basic/01_end_to_end.py`
- **THEN** the example SHALL enqueue at least one task
- **AND** it SHALL start a worker that executes the task
- **AND** it SHALL retrieve the task result via `TaskQueue.get_result`
- **AND** it SHALL deserialize the result value using `TaskQueue.deserialize_result`

### Requirement: ETA Scheduling Example
The documentation SHALL provide an example demonstrating delayed execution using `eta` (timezone-aware UTC datetimes).

#### Scenario: User schedules a delayed task
- **WHEN** a user runs `examples/basic/02_eta_delayed_execution.py`
- **THEN** the example SHALL enqueue a task with an `eta` in the near future
- **AND** it SHALL demonstrate that the task is not executed before `eta`

### Requirement: Bounded Concurrency Example
The documentation SHALL provide an example demonstrating bounded concurrency using `Worker(max_concurrency=...)`.

#### Scenario: User observes concurrency limit
- **WHEN** a user runs `examples/basic/03_bounded_concurrency.py`
- **THEN** the example SHALL enqueue multiple tasks that take measurable time
- **AND** it SHALL run a worker with `max_concurrency > 1`
- **AND** it SHALL demonstrate that the concurrency is bounded by that limit

### Requirement: Failure Recording Example
The documentation SHALL provide an example demonstrating how task failures are recorded and retrieved.

#### Scenario: Task fails and result is inspectable
- **WHEN** a user runs `examples/basic/04_failures_and_tracebacks.py`
- **THEN** the example SHALL execute a task that raises an exception
- **AND** it SHALL retrieve a `Result` with `status == "failed"`
- **AND** it SHALL display `Result.error` and `Result.traceback`

### Requirement: Sync Client Example
The documentation SHALL provide an example demonstrating synchronous enqueueing via `SyncTaskQueue` with a separate async worker processing tasks.

#### Scenario: Sync code enqueues and receives results
- **WHEN** a user runs `examples/basic/05_sync_client_with_worker.py`
- **THEN** the example SHALL enqueue work from synchronous code using `SyncTaskQueue`
- **AND** a worker SHALL process tasks using the same SQLite database file
- **AND** the sync code SHALL retrieve the successful result value

### Requirement: Example Code Quality
All runnable examples SHALL be immediately runnable against the v1 package and SHALL not depend on unimplemented sitq features.

#### Scenario: Examples run on a fresh install
- **WHEN** a user installs `sitq` and runs any script under `examples/basic/`
- **THEN** the script SHALL complete successfully without external infrastructure
- **AND** it SHALL use only public `sitq` APIs
- **AND** it SHALL complete within a bounded runtime (e.g. 30 seconds)

## REMOVED Requirements

### Requirement: Multiple Workers Example
**Reason**: v1 documentation examples focus on a single worker with bounded concurrency; multi-worker coordination is deferred until multi-process guidance is stabilized.

#### Scenario: User needs higher throughput
- **WHEN** a user needs higher throughput
- **THEN** the documentation SHALL recommend scaling by increasing `max_concurrency` first
- **AND** it MAY mention running multiple worker processes as an advanced pattern (clearly labeled)

### Requirement: Task Status Monitoring Example
**Reason**: v1 does not expose a stable public task status/metrics API suitable for a runnable monitoring example.

#### Scenario: User asks for status APIs
- **WHEN** a user looks for task status monitoring capabilities
- **THEN** the documentation SHALL avoid presenting non-existent APIs as runnable code

### Requirement: Batch Processing Example
**Reason**: v1 does not expose a public batch enqueue API; examples should use repeated `enqueue` calls.

#### Scenario: User wants to enqueue many tasks
- **WHEN** a user wants to enqueue many tasks
- **THEN** runnable examples SHALL demonstrate repeated `enqueue` calls
- **AND** advanced optimization guidance MAY be documented separately

