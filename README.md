# NotionSync

NotionSync is a Git-like CLI tool for syncing Markdown files with Notion pages. It provides a simple way to version control and back up your Notion content, with commands familiar to Git users such as `commit`, `push`, `pull`, `log`, and `status`.

## Features

- Git-like commands: `commit`, `push`, `pull`, `log`, `status`
- Auto-creation and management of `index.md`
- Mapping Markdown files to Notion pages
- Simple version history of Notion content
- Support for Notion databases
- Advanced Markdown formatting conversion (code blocks, quotes, etc.)

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/notionsync.git
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
│   ├── unit/             # Unit tests
│   └── integration/      # Integration tests
├── setup.py              # Package setup
└── README.md             # This file
```

## Supported Markdown Elements

NotionSync supports the following Markdown elements:

- **Headings**: `#`, `##`, `###` (H1, H2, H3)
- **Text formatting**:
  - **Bold**: `**text**` or `__text__`
  - **Italic**: `*text*` or `_text_`
  - **Strikethrough**: `~~text~~`
  - **Inline code**: `` `code` ``
- **Lists**:
  - **Bullet**: `- item`
  - **Numbered**: `1. item`
- **Checkboxes**: `- [ ] task`, `- [x] completed task`
- **Code blocks**: ````language\ncode\n``` (with language support)
- **Quotes**: `> quoted text`
- **Tables**: Standard Markdown table format
- **Horizontal rules**: `---`
- **Links**: `[text](URL)`
- **Images**: `![alt text](URL)`
- **Math**:
  - **Block math**: `$$` enclosed equations
  - **Inline math**: `$` enclosed equations (displays as italic text only)

## Troubleshooting

- If you have issues with the API key or page URL, run a diagnostic:
  ```
  python -m notionsync.utils.api_test
  ```

- Common issues:
  - **"No accessible page found" error**: Check that your integration is properly shared with the page
  - **Page ID error**: Verify that your Notion page URL is correct
  - **Too many blocks**: Large Markdown files might exceed Notion's limit (will be automatically split)

## License

MIT 

## 統合テスト

統合テストは実際のNotion APIを使用してNotionSyncの機能をテストします。以下の手順で設定してください：

1. Notionインテグレーションを作成し、APIキーを取得します。
2. `.env`ファイルにAPIキーとページURLを設定します。
3. Notionのウェブサイトでテスト用ページを開き、右上の「Share」ボタンをクリックします。
4. インテグレーションを選択して「Invite」をクリックし、インテグレーションとページを共有します。
5. 統合テストを実行します:
   ```
   python -m pytest tests/integration/test_notion_integration.py -v
   ```

統合テストはデフォルトでスキップされますが、上記の設定が完了していれば自動的に実行されます。 