# Claude Guidelines for PyRMQ

This document contains important information for Claude to remember when working with this repository.

## Repository Overview

PyRMQ is a Python wrapper around `pika` that simplifies interactions with RabbitMQ. It provides:

- A `Publisher` class for sending messages to RabbitMQ
- A `Consumer` class for receiving messages from RabbitMQ
- Built-in connection retry logic
- DLX-DLK based retry logic for message consumption
- Support for message priorities
- Support for different exchange types and exchange-to-exchange bindings
- Support for quorum and classic queue types

## Important Commands

### Testing

Run tests with pytest:
```bash
pytest
```

Run with tox for multiple Python versions:
```bash
uv tool install tox tox-uv
tox
```

Test for a specific Python version:
```bash
tox -e py311
```

### Package Management with UV

The project uses UV for fast package management:

```bash
# Install UV
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create a virtual environment
uv venv

# Activate the virtual environment
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows

# Install development dependencies
uv add -e .[dev]

# Run tests
uv run pytest
```

### Code Style

The project uses:
- Black for code formatting (v24.2.0)
- isort for import sorting (v5.13.2)
- flake8 for linting (v7.0.0)

## Python Support

The project supports Python 3.11-3.14.

## Project Structure

- `/pyrmq/` - Main package
  - `__init__.py` - Package exports with importlib.metadata for versioning
  - `publisher.py` - Publisher implementation
  - `consumer.py` - Consumer implementation
  - `/tests/` - Test suite
- Build system uses hatchling as specified in pyproject.toml

## Conventions

1. Follow the existing code style (Black formatted)
2. Maintain comprehensive docstrings in the existing format
3. Include type hints for function parameters and return values
4. Use specific exception handling, not bare excepts
5. Ensure proper error handling and retry logic for RabbitMQ operations
6. Write tests for new functionality
7. Update documentation if API changes were made
8. Use importlib.metadata instead of pkg_resources

## Development Workflow

1. Write/update code
2. Add tests
3. Run tests with pytest
4. Ensure code is formatted with pre-commit hooks
5. Update documentation if API changes were made

## Documentation

Documentation is built with Sphinx 8.x and hosted on ReadTheDocs. The docs are located in the `/docs/` directory.

## Recent Modernization Changes

1. Updated build system to use hatchling
2. Migrated to Python 3.11+ support
3. Updated all dependencies to latest versions
4. Added UV support for faster package management
5. Fixed documentation code blocks and links
6. Updated RabbitMQ links to new /docs/ URL structure
7. Replaced pkg_resources with importlib.metadata
8. Updated pre-commit hooks to latest versions