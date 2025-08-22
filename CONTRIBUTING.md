# Contributing to Fractal-Down

We welcome contributions to Fractal-Down! This guide outlines our development workflow, coding standards, and how to get started.

## Table of Contents

- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Pull Request Process](#pull-request-process)
- [Documentation](#documentation)
- [Performance Considerations](#performance-considerations)

## Getting Started

### Prerequisites

- Python 3.10 or higher
- Git
- Basic understanding of DAGs (Directed Acyclic Graphs)

### Setting Up Development Environment

1. **Clone the repository**:
   ```bash
   git clone https://github.com/nwoolr20/Fractal-Down.git
   cd Fractal-Down
   ```

2. **Install in development mode**:
   ```bash
   # Option 1: Install all dependencies (recommended)
   pip install -r requirements.txt
   
   # Option 2: Install selectively
   pip install -e .[test,bench,torch]
   ```

3. **Verify installation**:
   ```bash
   pytest
   fd init-sample
   ```

## Development Workflow

### Branching Strategy

- `main`: Stable releases
- `develop`: Integration branch for features
- Feature branches: `feature/description` or `fix/description`

### Making Changes

1. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** following our coding standards

3. **Test thoroughly**:
   ```bash
   # Run full test suite
   pytest
   
   # Run specific tests
   pytest tests/test_your_module.py
   
   # Test CLI functionality
   fd init-sample
   fd eval --budget 2 --verify
   ```

4. **Commit with descriptive messages**:
   ```bash
   git commit -m "Add: new fractal priority function for video analytics
   
   - Implement motion-based energy computation
   - Add tests for temporal coherence
   - Update examples with video use case"
   ```

## Coding Standards

### Code Formatting

We use [Black](https://black.readthedocs.io/) for code formatting:

```bash
# Format your code
black fractal_down/ tests/

# Check formatting
black --check fractal_down/ tests/
```

### Code Style

- **Function names**: `snake_case`
- **Class names**: `PascalCase`
- **Constants**: `UPPER_SNAKE_CASE`
- **Private methods**: prefix with `_`

### Documentation

- Use descriptive docstrings for all public functions and classes
- Follow [Google style](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings) for docstrings
- Include type hints for function parameters and return values

```python
def compute_node_priority(dag: DAG, root: int, params: FractalParams) -> Dict[int, float]:
    """Compute fractal priorities for all reachable nodes.
    
    Args:
        dag: The directed acyclic graph
        root: Root node ID to compute priorities for
        params: Fractal computation parameters
        
    Returns:
        Dictionary mapping node IDs to priority values
        
    Raises:
        ValueError: If root node doesn't exist in DAG
    """
```

## Testing Guidelines

### Test Organization

- **Unit tests**: Test individual functions and classes
- **Integration tests**: Test component interactions
- **Smoke tests**: Test CLI and major workflows
- **Performance tests**: Verify memory constraints and algorithm complexity

### Writing Tests

1. **Test file naming**: `test_module_name.py`
2. **Test function naming**: `test_specific_behavior()`
3. **Use descriptive test names** that explain what is being tested

```python
def test_fractal_priority_respects_depth_thresholds():
    """Test that priority computation applies depth-dependent thresholds correctly."""
    # Test implementation
```

### Test Coverage

- Aim for >90% code coverage
- Test edge cases and error conditions
- Verify deterministic behavior
- Test memory constraints

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=fractal_down

# Run specific test category
pytest tests/test_dag.py

# Run tests with specific markers
pytest -m "not slow"
```

## Pull Request Process

### Before Submitting

1. **Ensure tests pass**:
   ```bash
   pytest
   ```

2. **Format code**:
   ```bash
   black fractal_down/ tests/
   ```

3. **Update documentation** if needed

4. **Add tests** for new functionality

### PR Description Template

```markdown
## Description
Brief description of changes and motivation.

## Type of Change
- [ ] Bug fix
- [ ] New feature  
- [ ] Performance improvement
- [ ] Documentation update
- [ ] Breaking change

## Testing
- [ ] All existing tests pass
- [ ] Added tests for new functionality
- [ ] Tested manually with CLI

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No breaking changes (or marked appropriately)
```

### Review Process

1. **Automated checks** must pass (CI, linting)
2. **Code review** by maintainer
3. **Manual testing** of significant changes
4. **Documentation review** if applicable

## Documentation

### README Updates

- Keep examples working and up-to-date
- Update table of contents when adding sections
- Verify all links work

### API Documentation

- Document all public functions with docstrings
- Include usage examples for complex APIs
- Explain performance characteristics

### Comments

- Explain **why**, not just **what**
- Comment complex algorithms and optimizations
- Use inline comments sparingly

## Performance Considerations

### Memory Efficiency

- Respect √N memory constraints in new algorithms
- Use generators where appropriate
- Avoid unnecessary copying of large data structures

### Algorithm Complexity

- Document time/space complexity in docstrings
- Benchmark significant changes
- Profile memory usage for new features

### Testing Performance

```bash
# Run memory stress tests
pytest tests/test_memory_improvements.py

# Run benchmark suite
python refresh_benchmarks.py

# Profile specific scenarios
fd bench --scenarios memory-stress --verify
```

## Questions or Issues?

- **Bug reports**: Open an issue with reproduction steps
- **Feature requests**: Open an issue with use case description
- **Questions**: Start a discussion or comment on relevant issues

Thank you for contributing to Fractal-Down! 🚀