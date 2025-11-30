# Implementation Order for OpenSpec Proposals

This document defines the recommended implementation order for the current OpenSpec proposals in the sitq project.

## Overview

The implementation follows a **bottom-up dependency approach** where each proposal builds on previously implemented capabilities. This minimizes integration risk and allows incremental testing at each stage.

## Implementation Order

### 1. **add-serialization-core** (Foundation)
- **Priority**: 🔴 Critical (First)
- **Why first**: All other components depend on serialization for task payloads and results
- **Dependencies**: None
- **Complexity**: Low - Simple protocol + cloudpickle implementation
- **Key deliverables**: 
  - `Serializer` protocol with `dumps` and `loads` methods
  - `CloudpickleSerializer` implementation
  - Integration points in TaskQueue and Worker constructors
- **Estimated effort**: 2-3 days

### 2. **add-task-queue-core** (Core API)  
- **Priority**: 🔴 Critical (Second)
- **Why second**: Defines the primary user-facing API that other components build upon
- **Dependencies**: `serialization-core` (for payload serialization)
- **Complexity**: Medium - Core async queue logic + Result model
- **Key deliverables**:
  - `TaskQueue` class with async API (`enqueue`, `get_result`, `close`)
  - `Result` data model with status, payload, error fields
  - Backend interface for persistence
  - ETA scheduling with `available_at` timestamps
- **Estimated effort**: 3-4 days

### 3. **add-backend-sqlite** (Persistence Layer)
- **Priority**: 🟡 High (Third)
- **Why third**: Provides the persistence backend that TaskQueue and Worker need
- **Dependencies**: 
  - `task-queue-core` (backend interface definition)
  - `serialization-core` (payload storage format)
- **Complexity**: Medium-High - SQLite schema, concurrent access, atomic operations
- **Key deliverables**:
  - `Backend` protocol defining async operations
  - `SQLiteBackend` implementation with WAL mode
  - Task table schema and atomic reservation behavior
  - Multi-process safety considerations
- **Estimated effort**: 4-5 days

### 4. **add-worker-core** (Task Execution)
- **Priority**: 🟡 High (Fourth)
- **Why fourth**: Completes the core system by adding task execution capability
- **Dependencies**: 
  - `task-queue-core` (uses TaskQueue concepts)
  - `serialization-core` (serializes task execution)
  - `backend-sqlite` (reserves and marks tasks)
- **Complexity**: Medium - Async worker with concurrency control and graceful shutdown
- **Key deliverables**:
  - `Worker` class with `start` and `stop` methods
  - Polling loop with backend reservation
  - Concurrency control using `asyncio.Semaphore`
  - Graceful shutdown handling
  - Task lifecycle logging
- **Estimated effort**: 3-4 days

### 5. **add-sync-task-queue** (Convenience Wrapper)
- **Priority**: 🟢 Medium (Last)
- **Why last**: Pure convenience layer that wraps the already-implemented async core
- **Dependencies**: `task-queue-core` (wraps the async TaskQueue)
- **Complexity**: Low - Thin sync wrapper around async API
- **Key deliverables**:
  - `SyncTaskQueue` class as context manager
  - Internal event loop management
  - Delegation to async TaskQueue methods
  - Usage documentation and examples
- **Estimated effort**: 1-2 days

## Implementation Timeline

| Week | Focus | Deliverables |
|------|-------|--------------|
| Week 1 | `add-serialization-core` | Serializer protocol, CloudpickleSerializer |
| Week 2 | `add-task-queue-core` | TaskQueue API, Result model, backend interface |
| Week 3 | `add-backend-sqlite` | SQLite backend implementation |
| Week 4 | `add-worker-core` | Worker implementation with concurrency control |
| Week 5 | `add-sync-task-queue` | Sync wrapper and final integration |

## Risk Mitigation

### High-Risk Items
1. **SQLite concurrency** - Test multi-process access early
2. **Graceful shutdown** - Implement robust signal handling in Worker
3. **Memory management** - Monitor serializer memory usage with large payloads

### Integration Testing Strategy
- After each proposal: Run integration tests with previously implemented components
- After proposal 3: Test full enqueue → reserve → complete flow
- After proposal 5: End-to-end testing of both async and sync APIs

## Dependencies Graph

```
add-serialization-core (none)
    ↓
add-task-queue-core ← serialization-core
    ↓
add-backend-sqlite ← task-queue-core, serialization-core
    ↓
add-worker-core ← task-queue-core, serialization-core, backend-sqlite
    ↓
add-sync-task-queue ← task-queue-core
```

## Success Criteria

Each proposal is considered complete when:
1. All tasks in `tasks.md` are checked off
2. Unit tests pass with >90% coverage
3. Integration tests work with dependent components
4. Documentation is updated
5. `openspec validate <change-id> --strict` passes

## Notes

- This order assumes a single developer working full-time
- Parallel development is possible after the first two proposals are complete
- Each proposal should be validated and archived before starting the next
- Consider creating feature branches for each proposal to enable parallel testing