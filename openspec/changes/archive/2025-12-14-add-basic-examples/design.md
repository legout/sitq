# Design: Add Basic Examples

## Learning Progression Design

### Basic Examples Philosophy
The basic examples should follow these principles:
- **Single Concept**: Each example focuses on one core concept
- **Minimal Dependencies**: Avoid external libraries beyond sitq
- **Progressive Complexity**: Each example builds on previous concepts
- **Real-world Relevance**: Simple but practical use cases
- **Clear Documentation**: Extensive comments and explanations

### Example Categories and Flow

#### 1. Getting Started Examples
**Purpose**: Introduce core sitq concepts with minimal complexity

1. **Simple Task Processing** (`simple-task.md`)
   - Create queue and worker
   - Enqueue and process a simple task
   - Demonstrate basic sitq workflow

2. **Task with Arguments** (`task-arguments.md`)
   - Pass positional and keyword arguments
   - Show different argument types
   - Return and use results

#### 2. Core Concepts Examples
**Purpose**: Explore fundamental sitq capabilities

3. **Multiple Workers** (`multiple-workers.md`)
   - Create multiple worker instances
   - Demonstrate parallel processing
   - Show worker coordination

4. **Task Results** (`task-results.md`)
   - Get results from completed tasks
   - Handle successful and failed results
   - Result timeout handling

#### 3. Practical Patterns Examples
**Purpose**: Common usage patterns and best practices

5. **Error Handling** (`error-handling.md`)
   - Handle task exceptions
   - Retry failed tasks
   - Custom error callbacks

6. **Task Status** (`task-status.md`)
   - Monitor task progress
   - Check queue statistics
   - Track task lifecycle

#### 4. Advanced Basics Examples
**Purpose**: Bridge to more complex use cases

7. **Batch Processing** (`batch-processing.md`)
   - Process multiple tasks efficiently
   - Batch enqueue operations
   - Collect and aggregate results

8. **Sync vs Async** (`sync-async.md`)
   - Compare sync and async APIs
   - When to use each approach
   - Performance considerations

### Documentation Structure Design

#### Navigation Organization
```
User Guide:
  examples/
    basic/
      simple-task.md
      task-arguments.md
      multiple-workers.md
      task-results.md
      error-handling.md
      task-status.md
      batch-processing.md
      sync-async.md
    advanced/
      web-app.md
      data-processing.md
      microservices.md
```

#### Example Template Structure
Each basic example will follow this template:
```markdown
# Example Title

Brief description of what this example demonstrates.

## What You'll Learn
- Concept 1
- Concept 2
- Concept 3

## Prerequisites
- Previous examples (if any)
- Required knowledge

## Code Example
```python
# Well-commented code
```

## Key Concepts
- Explanation of core concepts
- Why this pattern matters
- When to use it

## Try It Yourself
- Simple exercise or modification
- Ways to extend the example

## Next Steps
- Link to next logical example
- Related advanced examples
```

### Content Strategy

#### Code Quality Standards
- **Minimal Imports**: Only import what's necessary
- **Clear Variable Names**: Self-documenting code
- **Extensive Comments**: Explain each step
- **Error Handling**: Show proper error patterns
- **Type Hints**: Use modern Python typing

#### Learning Objectives
Each example will have clear learning objectives:
- **Primary Goal**: Main concept to understand
- **Secondary Goals**: Supporting concepts
- **Prerequisites**: What you should know first
- **Outcomes**: What you'll be able to do

#### Progressive Complexity
- **Start Simple**: Minimal working example
- **Add Features**: Gradually introduce complexity
- **Real Context**: Connect to practical use cases
- **Advanced Path**: Show how this leads to advanced topics

### Integration with Existing Content

#### Cross-Reference Strategy
- Basic examples reference each other sequentially
- Basic examples link to relevant advanced examples
- Advanced examples reference basic concepts
- Quickstart links to most relevant basic examples

#### Content Avoidance
- Don't duplicate existing advanced examples
- Don't introduce complex external dependencies
- Don't cover enterprise-scale patterns in basics
- Don't assume prior task queue knowledge

### Validation Strategy

#### Code Validation
- All examples must run without errors
- Examples should be self-contained
- Code should follow project style guidelines
- Examples should demonstrate best practices

#### Documentation Validation
- All links must work correctly
- Navigation must be logical
- Content must be progressively ordered
- Examples must achieve learning objectives

## Implementation Considerations

### File Organization
- Keep examples in separate files for maintainability
- Use consistent naming conventions
- Include example data files where needed
- Provide clear file structure documentation

### Maintenance Strategy
- Examples should be version-independent where possible
- Update examples with API changes
- Keep examples focused on core concepts
- Regular review for clarity and accuracy

### Performance Considerations
- Basic examples should be lightweight
- Avoid resource-intensive operations
- Use appropriate timeouts and delays
- Consider memory usage in examples