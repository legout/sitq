# sitq.validation

Validation utilities for sitq.

```{eval-rst}
.. automodule:: sitq.validation
```

## validate

```{eval-rst}
.. autofunction:: validate
```

Validate input using fluent validation builder.

**Parameters:**
- `value` (Any): Value to validate
- `name` (str): Parameter name (for error messages)

**Returns:**
- [`ValidationBuilder`](sitq.validation.md): Validation builder for chaining validations

**Example:**
```python
from sitq import validate

# Validate backend
validate(backend, "backend").is_required().validate()

# Validate concurrency
validate(max_concurrency, "max_concurrency").is_required().in_range(1, 100).validate()

# Validate with custom error message
validate(poll_interval, "poll_interval").is_required().is_positive_number("Poll interval must be positive").validate()
```

## ValidationBuilder

```{eval-rst}
.. autoclass:: ValidationBuilder
```

Fluent builder for creating validation chains.

### Methods

#### `is_required()`

Ensure value is not None.

**Returns:**
- [`ValidationBuilder`](sitq.validation.md): Self for chaining

**Example:**
```python
validate(backend, "backend").is_required().validate()
```

#### `is_type(expected_type)`

Ensure value is of expected type.

**Parameters:**
- `expected_type` (type): Expected type

**Returns:**
- [`ValidationBuilder`](sitq.validation.md): Self for chaining

**Example:**
```python
from typing import Dict

validate(config, "config").is_type(Dict).validate()
```

#### `is_positive_number()`

Ensure value is a positive number.

**Returns:**
- [`ValidationBuilder`](sitq.validation.md): Self for chaining

**Example:**
```python
validate(concurrency, "concurrency").is_positive_number().validate()
```

#### `is_in_range(min_val, max_val)`

Ensure value is within specified range (inclusive).

**Parameters:**
- `min_val` (int or float): Minimum value
- `max_val` (int or float): Maximum value

**Returns:**
- [`ValidationBuilder`](sitq.validation.md): Self for chaining

**Example:**
```python
validate(max_concurrency, "max_concurrency").in_range(1, 1000).validate()
```

#### `with_message(message)`

Add custom error message for validation failure.

**Parameters:**
- `message` (str): Custom error message

**Returns:**
- [`ValidationBuilder`](sitq.validation.md): Self for chaining

**Example:**
```python
validate(backend, "backend").is_required().with_message("Backend is required").validate()
```

#### `validate()`

Perform validation and raise [`ValidationError`](sitq.exceptions.md) if validation fails.

**Raises:**
- [`ValidationError`](sitq.exceptions.md): If any validation fails

## Usage Examples

```python
from sitq import validate

# Single validation
validate(backend, "backend").is_required().validate()

# Chained validations
validate(max_concurrency, "max_concurrency").is_required().in_range(1, 100).validate()

# With custom message
validate(poll_interval, "poll_interval").is_positive_number().with_message("Poll interval must be positive").validate()
```

## Built-in Validation Functions

```python
from sitq.validation import validate_callable, validate_positive_number

# Validate callable
validate(my_function, "function").validate()

# Validate positive number
validate(concurrency, "concurrency").validate_positive_number()
```

## Best Practices

1. **Validate all user inputs** before using them
2. **Provide descriptive error messages** for validation failures
3. **Use specific validators** (not just generic checks)
4. **Chain multiple validations** for complex rules
5. **Test validation logic** with edge cases

## See Also

- [`ValidationError`](sitq.exceptions.md) - Validation exception
- [Error Handling Guide](../../reference/ERROR_HANDLING.md) - Comprehensive error handling
