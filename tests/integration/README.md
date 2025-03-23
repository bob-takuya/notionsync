# NotionSync Integration Tests

This directory contains integration tests for NotionSync that verify the complete functionality of the tool with actual Notion API interactions.

## Test Files

- **test_notion_blocks.py**: Verifies the conversion of different Notion block types to/from Markdown.
- **test_notion_integration.py**: Tests the core integration with the Notion API.
- **test_simple_workflow.py**: Tests a basic workflow including init, commit, push, and pull with minimal content.
- **test_complete_workflow.py**: Tests a comprehensive workflow with various Markdown elements and commands.

## Running Integration Tests

To run the integration tests, you need:

1. A Notion API key
2. A Notion page URL or database ID
3. A proper `.env` file in the project root

### Setting up the environment

Create a `.env` file in the project root with the following content:

```
NOTION_API_KEY=your_api_key_here
NOTION_PAGE_URL=your_notion_page_url
```

Make sure your integration has access to the Notion page by sharing it with the integration in the Notion UI.

### Running specific tests

```bash
# Run all integration tests
python -m pytest tests/integration

# Run a specific test file
python -m pytest tests/integration/test_simple_workflow.py

# Run a specific test case with verbose output
python -m pytest tests/integration/test_complete_workflow.py::TestCompleteWorkflow::test_complete_workflow -v
```

## Test Coverage

The integration tests cover:

- Initialization of a NotionSync project
- Creating and managing Markdown files
- Committing changes to the local version history
- Pushing content to Notion
- Pulling content from Notion
- Converting various Markdown elements to Notion blocks and vice versa
- Handling errors and edge cases

## Adding New Tests

When adding new tests, please follow these guidelines:

1. Create a unique test page for each test run to avoid interference
2. Clean up after tests by archiving created pages
3. Add proper assertions to verify functionality
4. Handle potential API errors gracefully
5. Document the purpose and behavior of new tests

## Troubleshooting

If tests are failing, check:

1. Notion API key validity
2. Integration access to the test page
3. Rate limits (Notion API has rate limits that may affect test runs)
4. Network connectivity
5. API response errors in the test output 