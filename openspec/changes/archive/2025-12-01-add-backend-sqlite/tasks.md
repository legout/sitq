## 1. Implementation
- [x] 1.1 Define a `Backend` protocol and `ReservedTask` data model for queue persistence.
- [x] 1.2 Implement `SQLiteBackend` with schema creation, `enqueue`, `reserve`, `mark_success`, `mark_failure`, and `get_result`.
- [x] 1.3 Configure SQLite for WAL mode and safe concurrent access where possible.
- [x] 1.4 Add unit and basic integration tests for the SQLite backend operations.

