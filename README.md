# bchat

A simple command-line chatbot/repl that passes prompts to Copilot and displays responses. Designed for simplicity and extensibility.

## Configuration

The application requires an OpenAI API key. Create a `config.ini` file in the root directory with the following content:

```ini
[DEFAULT]
api_key = your-api-key-here
```

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
2. Install the package in editable mode with development dependencies:
   ```bash
   pip install -e ".[development]"
   ```

### Testing

We use `pytest` for testing. The testing strategy focuses on "Happy Path" tests for all components, entry points, and output methods to ensure core functionality works as expected.

To run the tests:

```bash
pytest
```

## Project Structure

- `main.py`: Entry point for the application.
- `pyproject.toml`: Project metadata and dependencies.
- `config.ini`: Configuration file.
