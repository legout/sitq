## 1. SQLiteBackend (HIGH priority)
- [x] 1.1 Add complete docstring to `__init__` with Args for `db_path` and other parameters
- [x] 1.2 Add docstring to `enqueue` with Args, Returns, Raises
- [x] 1.3 Add docstring to `fetch_due_tasks` with Args, Returns
- [x] 1.4 Add docstring to `update_task_state` with Args
- [x] 1.5 Add docstring to `store_result` with Args, Returns
- [x] 1.6 Add docstring to `claim_task` with Args, Returns
- [x] 1.7 Add docstring to `release_task` with Args
- [x] 1.8 Add docstring to `schedule_retry` with Args
- [x] 1.9 Expand minimal docstrings for `reserve`, `mark_success`, `mark_failure` with Args/Returns

## 2. Exception constructors (HIGH priority)
- [x] 2.1 Document `TaskQueueError.__init__` parameters
- [x] 2.2 Document `BackendError.__init__` parameters
- [x] 2.3 Document all remaining exception `__init__` methods (10 more classes) with Args sections

## 3. Serialization (HIGH priority)
- [x] 3.1 Add Args and Returns to `serialize_task_envelope`
- [x] 3.2 Add Args and Returns to `deserialize_result`
- [x] 3.3 Add docstring to `serialize_result`

## 4. Backend base class (MEDIUM priority)
- [x] 4.1 Add Args/Returns to `Backend.connect`
- [x] 4.2 Add Args/Returns to `Backend.close`
- [x] 4.3 Add Args/Returns/Raises to `Backend.enqueue`
- [x] 4.4 Add Args/Returns/Raises to `Backend.reserve`
- [x] 4.5 Add Args/Returns/Raises to `Backend.mark_success`
- [x] 4.6 Add Args/Returns/Raises to `Backend.mark_failure`
- [x] 4.7 Add Args/Returns to `Backend.get_result`
- [x] 4.8 Add docstrings to `Backend.__aenter__` and `__aexit__`

## 5. Validation
- [x] 5.1 Ensure all new docstrings follow Google-style format
- [x] 5.2 Run `mkdocs build` and verify API reference pages render correctly
- [x] 5.3 Check for consistency in parameter naming and description style
