# bchat

A command-line chatbot/REPL that interacts with OpenAI's GPT models. Designed for simplicity and extensibility to support future interfaces (web, GUI, etc.).

## Key Features

- **Interactive REPL**: Command-line interface with rich terminal UI and markdown rendering
- **Session Management**: Save and load conversation sessions
- **Conversation History**: Maintain context across interactions with configurable history limits
- **File Context**: Load files into conversation context for AI-assisted code review and discussion
- **Rich Terminal UI**: Beautiful output formatting with markdown support using the Rich library

## Installation

To install the `bchat` application, follow these steps:

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd bchat
   ```

2. Create and activate a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. Install the application:
   ```bash
   pip install .
   ```

4. Create a `secrets.ini` file in the project root with your OpenAI API key:
   ```ini
   [DEFAULT]
   api_key = your_api_key_here
   ```

5. Verify the installation:
   ```bash
   bchat --help
   ```

## Usage

Start the application by running:
```bash
bchat
```

You will enter an interactive REPL (Read-Eval-Print Loop). The prompt displays the current model and session information in a bottom toolbar.

### Available Commands

Commands start with a slash (`/`). Any text not starting with a slash is treated as a prompt to the AI.

#### Session Management
- `/version` - Display the application version
- `/help` - Show available commands
- `/save [name]` - Save current session (auto-generates name if not provided)
- `/load [name]` - Load a session (loads most recent if name not provided)
- `/history` - List saved sessions with timestamps
- `/exit` or `/quit` - Exit the application

#### Runtime Configuration
- `/set <option> <value>` - Configure runtime settings (temperature, model, personality)

**Available Options:**
- `temp` or `temperature` - AI response randomness (0.0-2.0)
  - Presets: `default` (0.7), `rigid` (0.3), `creative` (1.5)
  - Examples: `/set temp creative`, `/set temperature 0.9`
- `model` - AI model to use
  - Presets organized by provider:
    - `default` (claude-3-5-sonnet-20241022) - Default model, Claude Sonnet
    - `mini`/`fast` (claude-3-5-haiku-20241022) - Fastest/cheapest option
    - `gpt-mini` (gpt-4o-mini) - OpenAI mini model
    - `standard` (gpt-4o) - OpenAI standard model
    - `claude-haiku`/`claude-mini` (claude-3-5-haiku-20241022) - Claude mini model
    - `claude-sonnet` (claude-3-5-sonnet-20241022) - Claude standard model
    - `reasoning`/`research` (o1-pro) - Deep reasoning model
  - Examples: `/set model gpt-mini`, `/set model claude-haiku`, `/set model gpt-4o-mini`
- `personality` - AI response style
  - Presets: `default` (helpful and concise), `concise` (brief responses), `detailed` (comprehensive), `creative` (imaginative and elaborate)
  - Examples: `/set personality concise`, `/set personality creative`

**Auto-correction:** The system provides friendly suggestions when values are close to valid presets or ranges.

#### File Context
- `/add <path|glob>` - Add file(s) to conversation context
- `/remove <path>` - Remove file from context
- `/context` - Show current context (loaded files and message history)
- `/refresh` - Reload file contents to detect changes

### File Context Feature

Load files into the conversation context so the AI can reference your code or documents.

**Adding Files:**
```bash
/add src/main.py           # Single file
/add src/**/*.py           # Glob pattern
/add *.md                  # Multiple files
```

**Viewing Context:**
```bash
/context                   # Shows loaded files AND message history count
```

**Example:**
```
bChat (claude-3-5-sonnet-20241022) > /add main.py session.py
│ ✔ Added: main.py (85 lines)
│ ✔ Added: session.py (82 lines)

bChat (claude-3-5-sonnet-20241022) > /context
┌─ Context ──────────────────────────────┐
│ Files:                                 │
│   main.py (85 lines, 2.4 KB)           │
│   session.py (82 lines, 3.0 KB)        │
│                                        │
│ Messages: 4 in history                 │
│ Total: 2 files, 167 lines, 5.4 KB      │
└────────────────────────────────────────┘
```

### Runtime Configuration Feature

Adjust AI behavior during a conversation without restarting the application.

**Changing Temperature:**
```bash
/set temp 0.9              # Numeric value between 0.0 and 2.0
/set temperature creative  # Use preset (rigid/default/creative)
```

**Changing Model:**
```bash
/set model mini            # Use fastest/cheapest model (claude-3-5-haiku-20241022)
/set model claude-haiku    # Use Claude mini model
/set model standard        # Use OpenAI standard model (gpt-4o)
/set model reasoning       # Use deep reasoning model (o1-pro)
/set model gpt-4o-mini     # Use full model name directly
```

**Changing Personality:**
```bash
/set personality concise   # Brief, direct responses
/set personality detailed  # Comprehensive, thorough responses
/set personality creative  # Imaginative, elaborate responses
```

**Example:**
```
bChat (claude-3-5-sonnet-20241022) > /set temperature creative
│ ✔ Temperature set to 1.5 (creative)

bChat (claude-3-5-sonnet-20241022) > /set model gpt-mini
│ ✔ Model set to gpt-4o-mini

bChat (claude-3-5-sonnet-20241022) > /set personality detailed
│ ✔ Personality set to detailed
```

## Configuration

### Main Configuration (`config.ini`)

General settings for the application:

```ini
[DEFAULT]
log_file = bchat.log
log_level = INFO
log_truncate_len = 40
temperature = 0.7
max_history = 100
system_instruction = You are a helpful and concise assistant. You enjoy helping the user with their requests.
```

**Configuration Options:**
- `log_file`: Log file path (default: bchat.log)
- `log_level`: Logging verbosity (DEBUG, INFO, ERROR)
- `log_truncate_len`: Maximum length for truncated log messages
- `temperature`: OpenAI temperature setting (0.0 to 1.0)
- `max_history`: Maximum number of conversation messages to retain
- `system_instruction`: System message sent to the AI model
- `file_context_max_size`: Maximum total size in characters for file context (default: 50000)

### Secrets (`secrets.ini`)

Sensitive information like API keys. This file is ignored by git.

```ini
[DEFAULT]
api_key = your_api_key_here
```

## Development

### Setting up the Development Environment

To set up the environment for development, including testing tools:

1. Activate your virtual environment (as described in Installation).
2. Run the install script:
   ```bash
   ./scripts/install.sh
   ```

### Testing

We use `pytest` for testing. The testing strategy focuses on "Happy Path" tests for all components, entry points, and output methods to ensure core functionality works as expected.

To run the tests:

```bash
./scripts/test.sh
```

### CI/CD

The project uses GitHub Actions for Continuous Integration. The workflow is defined in `.github/workflows/ci.yml` and runs the same bash scripts used for local development:

- `scripts/install.sh`: Installs dependencies.
- `scripts/test.sh`: Runs the test suite.

This ensures that the CI environment matches the local development environment as closely as possible.

## Project Structure

- `main.py` - Entry point, logging setup, and configuration loading
- `repl.py` - REPL interface and command handling
- `session.py` - Session and conversation history management
- `context_loader.py` - File context loading and management
- `config.ini` - Configuration settings
- `pyproject.toml` - Project metadata and dependencies

**Dependencies:**
- `openai>=1.0.0` - OpenAI API client
- `prompt_toolkit>=3.0.0` - Interactive command-line interface
- `rich>=13.0.0` - Rich terminal formatting and markdown rendering

**Requirements:**
- Python >= 3.7

**License:**
- MIT

## Architecture

### Component Responsibilities

- **main.py**: Application entry point. Loads configuration from `config.ini` and `secrets.ini`, initializes logging, creates `Session` and `Repl` instances, and starts the REPL loop.

- **session.py**: Manages application state independent of UI. Handles OpenAI client initialization, conversation history (rolling window), and session persistence (save/load to JSON files in `sessions/` directory).

- **repl.py**: Handles all user interaction. Uses `prompt_toolkit` for input (with bottom toolbar) and `Rich` for output (panels, markdown rendering, status messages).

- **file_context_loader.py**: Manages file contexts for injection into AI conversations. Handles file loading, glob patterns, size limits, and content refresh.

### Data Flow

```
User Input → Repl.handle_input() → Session.add_message()
                                 → Session.get_messages()
                                 → FileContextLoader.format_for_prompt() (injected into system prompt)
                                 → OpenAI API
                                 → Repl.print_response()
```

### UI Library Integration

The application uses two terminal libraries that must be kept separate:

- **prompt_toolkit**: Handles input prompt and bottom toolbar. Uses `HTML` markup and `Style` objects.
- **Rich**: Handles all output (panels, markdown, status messages). Uses Rich markup syntax.

**Important**: Do not pass Rich-rendered ANSI output through Rich's `console.print()` again—this causes double-processing. When combining pre-rendered content with prefixes, use Python's built-in `print()` with raw ANSI codes.

### Session Storage

Sessions are stored as JSON files in the `sessions/` directory:
```json
[
  {"role": "user", "content": "Hello"},
  {"role": "assistant", "content": "Hi there!"}
]
```

## Logging

The application logs events to a file specified in the configuration (default: `bchat.log`).

**Log Levels:**
- **INFO**: High-level events including startup, shutdown, and truncated user prompts
- **DEBUG**: Detailed information including full API request payloads and full API responses
- **ERROR**: Error details when exceptions occur

**Log Format:**
`%(asctime)s - %(name)s - %(levelname)s - %(message)s`
