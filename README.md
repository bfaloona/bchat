# bchat

A simple command-line chatbot/repl that passes prompts to Copilot and displays responses. Designed for simplicity and extensibility.

## Configuration

### Main Configuration (`config.ini`)
General settings for the application.

```ini
[DEFAULT]
log_file = bchat.log
log_level = INFO
temperature = 0.7
system_instruction = You are a helpful assistant.
```

### Secrets (`secrets.ini`)
Sensitive information like API keys. This file is ignored by git.

```ini
[DEFAULT]
api_key = your_api_key_here
```

## Logging

The application logs events to a file specified in the configuration (default: `bchat.log`).

**Log Levels:**
- **INFO**: High-level events including startup, shutdown, and truncated user prompts (max 20 chars).
- **DEBUG**: Detailed information including full API request payloads and full API responses.
- **ERROR**: Error details when exceptions occur.

**Log Format:**
`%(asctime)s - %(name)s - %(levelname)s - %(message)s`

## Usage

Start the application by running:
```bash
bchat
```

You will enter an interactive REPL (Read-Eval-Print Loop). The prompt displays the current model and temperature settings:

```text
== gpt-4o / 0.7 ==
bChat>
```

### Commands
Commands start with a slash (`/`). All command effects are persistent for the session.

- `/version`: Display the application version.
- `/help`: Show available commands.
- `/exit` or `/quit`: Exit the application.

Any text not starting with a slash is treated as a prompt to the AI.

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

4. Verify the installation:
   ```bash
   bchat --help
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

- `main.py`: Entry point for the application.
- `pyproject.toml`: Project metadata and dependencies.
- `config.ini`: Configuration file.
