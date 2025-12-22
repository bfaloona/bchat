# bchat

A command-line chatbot/REPL that interacts with OpenAI's models (primarily Copilot). Designed for simplicity and extensibility to support future interfaces (web, GUI, etc.).

## Key Features

- **Interactive REPL**: Command-line interface with rich terminal UI and markdown rendering
- **Session Management**: Save and load conversation sessions
- **Conversation History**: Maintain context across interactions with configurable history limits
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

- `/version` - Display the application version
- `/help` - Show available commands
- `/save [name]` - Save current session (auto-generates name if not provided)
- `/load [name]` - Load a session (loads most recent if name not provided)
- `/history` - List saved sessions with timestamps
- `/exit` or `/quit` - Exit the application

## Configuration

### Main Configuration (`config.ini`)

General settings for the application:

```ini
[DEFAULT]
log_level = INFO
log_truncate_len = 40
temperature = 0.7
max_history = 100
system_instruction = You are a helpful and concise assistant. You enjoy helping the user with their requests.
```

**Configuration Options:**
- `log_level`: Logging verbosity (DEBUG, INFO, ERROR)
- `log_truncate_len`: Maximum length for truncated log messages
- `temperature`: OpenAI temperature setting (0.0 to 1.0)
- `max_history`: Maximum number of conversation messages to retain
- `system_instruction`: System message sent to the AI model

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
- `config.ini` - Configuration settings
- `pyproject.toml` - Project metadata and dependencies

**Dependencies:**
- `openai>=1.0.0` - OpenAI API client
- `prompt_toolkit>=3.0.0` - Interactive command-line interface
- `rich>=13.0.0` - Rich terminal formatting and markdown rendering

**Requirements:**
- Python >= 3.7
- MIT License

## Logging

The application logs events to a file specified in the configuration (default: `bchat.log`).

**Log Levels:**
- **INFO**: High-level events including startup, shutdown, and truncated user prompts
- **DEBUG**: Detailed information including full API request payloads and full API responses
- **ERROR**: Error details when exceptions occur

**Log Format:**
`%(asctime)s - %(name)s - %(levelname)s - %(message)s`
