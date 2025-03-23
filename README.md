# NotionSync

NotionSync is a Git-like CLI tool for syncing Markdown files with Notion pages. It provides a simple way to version control and back up your Notion content, with commands familiar to Git users such as `commit`, `push`, `pull`, `log`, and `status`.

## Features

- Git-like commands: `commit`, `push`, `pull`, `log`, `status`
- Auto-creation and management of `index.md`
- Mapping Markdown files to Notion pages
- Simple version history of Notion content
- Support for Notion databases
- Advanced Markdown formatting conversion (code blocks, quotes, etc.)
- Support for Notion child pages

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/bob-takuya/notionsync.git
   cd notionsync
   ```

2. Install the package:
   ```
   pip install -e .
   ```

## Configuration

Before using NotionSync, you need to set up your Notion API credentials:

1. Create a Notion integration:
   - Go to https://www.notion.so/my-integrations
   - Click "New integration"
   - Enter a name (e.g., NotionSync)
   - Click "Submit"
   - Copy the "Internal Integration Token" (API key)

2. Share your Notion page with the integration:
   - Open your Notion page
   - Click the "Share" button
   - Select "Add people, emails, groups, or integrations"
   - Select your integration name
   - Click "Invite"

3. Run `notionsync init` in your project directory

4. Edit the created `.env` file:
   ```
   NOTION_API_KEY=your_notion_api_key_here
   NOTION_PAGE_URL=https://www.notion.so/your_page_url
   # Uncomment the following line if using a database
   # NOTION_DATABASE_ID=your_database_id_here
   ```

## Usage

### Initialize a New Project

```
notionsync init
```

This creates a template `index.md` file and a `.env` configuration file.

### Check Status

```
notionsync status
```

Shows files that have been changed, added, or deleted since the last commit.

### Commit Changes

```
notionsync commit -m "Your commit message"
```

Records the current state of your Markdown files.

### Push Changes to Notion

```
notionsync push
```

Uploads your committed changes to Notion. Works with both regular pages and databases.

### Pull Content from Notion

```
notionsync pull
```

Downloads the latest content from Notion to your local Markdown files.

### View Commit History

```
notionsync log
```

Displays your commit history.

## Project Structure

```
notionsync/
├── notionsync/           # Main package
│   ├── __init__.py       # Package initialization
│   ├── cli/              # Command line interface
│   │   ├── __init__.py
│   │   └── commands.py   # CLI commands
│   ├── core/             # Core functionality
│   │   ├── __init__.py
│   │   ├── notion_client.py  # Notion API client
│   │   └── sync.py       # Sync functionality
│   ├── markdown/         # Markdown processing
│   │   ├── __init__.py
│   │   └── converter.py  # Markdown to Notion conversion
│   └── utils/            # Utility functions
│       ├── __init__.py
│       └── helpers.py    # Helper utilities
├── tests/                # Test suite
│   └── integration/      # Integration tests with real Notion API
├── setup.py              # Package setup
└── README.md             # This file
```

## Supported Markdown Elements

NotionSync supports the following Markdown elements:

### Text and Paragraphs

- **Paragraphs**: Separated by blank lines
  ```
  This is a paragraph.

  This is another paragraph.
  ```

### Headings

- **Headings**: `#`, `##`, `###` (H1, H2, H3)
  ```markdown
  # Heading 1
  ## Heading 2
  ### Heading 3
  ```

### Text Formatting

- **Bold**: `**text**` or `__text__`
  ```markdown
  **Bold text** or __Bold text__
  ```

- **Italic**: `*text*` or `_text_`
  ```markdown
  *Italic text* or _Italic text_
  ```

- **Strikethrough**: `~~text~~`
  ```markdown
  ~~Strikethrough text~~
  ```

- **Inline code**: `` `code` ``
  ```markdown
  `inline code`
  ```

- **Combined formatting**: 
  ```markdown
  **Bold text with *italic* inside**
  ```

### Lists

- **Bullet lists**: 
  ```markdown
  - Item 1
  - Item 2
  - Item 3
  ```

- **Numbered lists**: 
  ```markdown
  1. First item
  2. Second item
  3. Third item
  ```

- **Nested lists**: 
  ```markdown
  - Main item
    - Sub-item 1
    - Sub-item 2
  - Another main item
  ```

- **Mixed lists**: 
  ```markdown
  1. First numbered item
     - Bullet sub-item
     - Another bullet sub-item
  2. Second numbered item
  ```

### Task Lists

- **Checkboxes/To-do items**: 
  ```markdown
  - [ ] Uncompleted task
  - [x] Completed task
  ```

- **Nested tasks**: 
  ```markdown
  - [ ] Main task
    - [ ] Subtask 1
    - [x] Subtask 2
  ```

### Code Blocks

- **Code blocks**: 
  ```markdown
  ```python
  def hello():
      print('Hello, world!')
  ```
  ```

- **Supported languages**: Python, JavaScript, Java, C, C++, C#, Ruby, Go, Rust, PHP, TypeScript, HTML, CSS, SQL, Bash, and many more.

### Blockquotes

- **Blockquotes**: 
  ```markdown
  > This is a blockquote
  > It can span multiple lines
  ```

- **Nested blockquotes**: 
  ```markdown
  > Outer quote
  > > Nested quote
  ```

### Tables

- **Tables**: 
  ```markdown
  | Header 1 | Header 2 |
  |----------|----------|
  | Cell 1   | Cell 2   |
  | Cell 3   | Cell 4   |
  ```

### Links and Images

- **Links**: 
  ```markdown
  [Link text](https://example.com)
  ```

- **Images**: 
  ```markdown
  ![Alt text](https://example.com/image.jpg)
  ```

### Horizontal Rules

- **Horizontal rules**: 
  ```markdown
  ---
  ```

### Special Blocks

- **Callout blocks**: (Custom syntax for Notion callouts)
  ```markdown
  ::: callout 💡
      This is a callout with an emoji.
  :::
  ```

- **Math equations**: (Limited support)
  ```markdown
  $E = mc^2$
  ```

## Working with Child Pages

NotionSync supports working with Notion's hierarchical page structure. When you pull content from Notion, both the main page and its child pages will be retrieved:

- The main page content is saved to `index.md`
- Each child page is saved as a separate Markdown file
- The filename is derived from the page title

### Embedded Child Pages

Notion allows child pages to appear between paragraphs or other content. When you pull content from Notion, these embedded child pages will be represented in the Markdown as links to the corresponding child page file:

```markdown
This is content before the child page.

## Section Before

[📄 Embedded Child Page](Embedded Child Page.md)

## Section After

This is content after the child page.
```

The child page itself will be saved as a separate Markdown file, just like any other child page:

```markdown
# Embedded Child Page

This is content inside the embedded child page.
```

When pushing content back to Notion, child pages will be created as separate pages under the parent page, with the file name (minus the `.md` extension) used as the page title.

### Example

A Notion workspace with this structure:
```
Main Page
├── Child Page A
│   └── Nested Page 1
└── Child Page B
```

Will be pulled as:
```
index.md          # Contains Main Page content
Child Page A.md   # Contains Child Page A content
Nested Page 1.md  # Contains Nested Page 1 content
Child Page B.md   # Contains Child Page B content
```

### Creating Child Pages

Any Markdown file (other than `index.md`) in your workspace will be pushed to Notion as a child page of your main page. The filename (without the `.md` extension) will be used as the page title.

For example:
```
index.md          # Main page content
Project Plan.md   # Will become a child page titled "Project Plan"
Meeting Notes.md  # Will become a child page titled "Meeting Notes"
```

### Limitations

- Currently supports up to 5 levels of nested pages
- All child pages are saved as flat files in the root directory, regardless of their nesting in Notion
- Child database pages are detected but not fully supported yet

## Troubleshooting

- If you have issues with the API key or page URL, run a diagnostic:
  ```
  python -m notionsync.utils.api_test
  ```

- Common issues:
  - **"No accessible page found" error**: Check that your integration is properly shared with the page
  - **Page ID error**: Verify that your Notion page URL is correct
  - **Too many blocks**: Large Markdown files might exceed Notion's limit (will be automatically split)
  - **Missing child pages**: Ensure you're using the latest version that supports child pages

## License

MIT 

## Integration Tests

NotionSync implements test cases that use the actual Notion API. You can run the integration tests by following these steps:

1. **Create a Notion integration and obtain an API key:**
   - Visit [https://www.notion.so/my-integrations](https://www.notion.so/my-integrations)
   - Click on **"New integration"**
   - Enter a name (e.g., *NotionSync Test*)
   - Click **"Submit"**
   - Copy the **"Internal Integration Token"** (API key)

2. **Set the API key and page URL in the `.env` file:**
   ```bash
   NOTION_API_KEY=your_notion_api_key_here
   NOTION_PAGE_URL=https://www.notion.so/your_page_url
   # For database testing (if needed)
   # NOTION_DATABASE_ID=your_database_id_here
   ```

3. **Open a test page on the Notion website and share it with your integration:**
   - Open the Notion page
   - Click the **"Share"** button in the top right corner
   - Select the integration and click **"Invite"**

4. **Run the integration tests:**
   ```bash
   python -m pytest tests/integration/test_notion_workflow.py -v
   ```

This will test the following use cases:

- Initial setup and automatic generation of `index.md`
- Local document creation and the status command
- Execution of the commit command
- Execution of the push command
- Pull command after editing on Notion
- Verification of the log command
- Re-editing flow after local edits
- Error handling and validation of improper operations
- Database integration tests (when `NOTION_DATABASE_ID` is set)

The tests create temporary directories for each step, which are automatically deleted upon completion.