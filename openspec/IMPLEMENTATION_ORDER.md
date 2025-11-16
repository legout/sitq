# OpenSpec Implementation Order

This document outlines the recommended implementation order for the sitq v1 change proposals based on dependency analysis.

## Implementation Order

### 1. **add-serialization-core** (Foundation)
**Why first:** No dependencies on other proposals. Establishes the Serializer protocol and Cloudpickle implementation that other components will use.

**Dependencies:** None
**Used by:** task-queue-core, worker-core

### 2. **add-backend-sqlite** (Foundation)
**Why second:** No dependencies on other proposals. Establishes the Backend protocol and SQLiteBackend that other components will use.

**Dependencies:** None
**Used by:** task-queue-core, worker-core

### 3. **add-task-queue-core** (Core API)
**Why third:** Depends on both serialization-core and backend-sqlite. This is the main async TaskQueue API that defines the core user-facing functionality.

**Dependencies:**
- serialization-core (Serializer protocol)
- backend-sqlite (Backend protocol)

**Used by:** sync-task-queue, worker-core

### 4. **add-sync-task-queue** (Sync Wrapper)
**Why fourth:** Depends only on task-queue-core. Provides synchronous convenience wrapper around the async TaskQueue.

**Dependencies:**
- task-queue-core (TaskQueue API)

**Used by:** None

### 5. **add-worker-core** (Worker Implementation)
**Why last:** Depends on all previous components. The Worker brings together the TaskQueue, Backend, and Serializer to execute tasks with concurrency control.

**Dependencies:**
- serialization-core (Serializer)
- backend-sqlite (Backend)
- task-queue-core (TaskQueue API)

**Used by:** None

## Dependency Graph

```
add-serialization-core
        ↓
        ↓ (Serializer)
        ↓
add-task-queue-core ←── add-backend-sqlite
        ↓                       ↑
        ↓ (TaskQueue)          ↑ (Backend)
        ↓                       ↑
add-sync-task-queue             ↓
        ↓                       ↓
        └── add-worker-core ←───┘
```

## Rationale

1. **Foundation First**: serialization-core and backend-sqlite are independent foundations that define protocols and basic implementations.

2. **API Before Implementation**: task-queue-core defines the user-facing API before the worker implementation that uses it.

3. **Convenience Last**: sync-task-queue is a convenience wrapper and can be added after the core async API is stable.

4. **Integration End**: worker-core integrates all previous components and should be implemented last to ensure all dependencies are stable.

## Testing Strategy

- Each proposal should include unit tests for its specific functionality
- Integration tests should be added as components are combined (particularly for task-queue-core → sync-task-queue and all components → worker-core)
- End-to-end tests should verify the complete flow: TaskQueue → Worker → Result

## Migration Path

Each implementation step should:
1. Maintain compatibility with existing code in src_bak/
2. Follow the architectural patterns defined in openspec/project.md
3. Use the tech stack specified (Python 3.13+, asyncio, SQLite, cloudpickle)
4. Include proper error handling and logging as specified in each proposal