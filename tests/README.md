# NotionSync Tests

This directory contains tests for the NotionSync package.

## Directory Structure

- `unit/`: Unit tests for individual components
  - `test_markdown_conversion.py`: Tests for Markdown conversion
  - `test_notion_client.py`: Tests for Notion API client
  - etc.
- `integration/`: Integration tests for workflows
  - `test_workflow.py`: Tests for complete workflows

## Running Tests

To run all tests:

```bash
pytest
```

To run unit tests only:

```bash
pytest tests/unit
```

To run integration tests only:

```bash
pytest tests/integration
```

To run with more verbose output:

```bash
pytest -v
```

## Writing Tests

When adding new tests:

1. For unit tests, place them in the `unit/` directory
2. For integration tests, place them in the `integration/` directory
3. Use descriptive test names
4. Use fixtures from `conftest.py` where appropriate

## Test Coverage

To run tests with coverage report:

```bash
pytest --cov=notionsync
``` 