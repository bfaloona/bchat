# Copilot Instructions for bchat

## Project Overview
This is a simple chatbot Python project named `bchat`. Currently implemented asa command-line repl, the architecture must allow easy extension to other interfaces (e.g., web, GUI) in the future.

## Tech Stack
- **Language**: Python 3.7+
- **Build System**: pyproject.toml (setuptools)
- **Testing**: pytest and GitHub Actions
- **AI Provider**: OpenAI API
- **Configuration**: config.ini

## Coding Standards
- Use PEP 8 formatting.
- Prefer `pathlib` over `os.path`.
- Use type hints for function arguments and return values.
- Docstrings should follow the Google Python Style Guide.

## Project Structure
- `main.py`: Entry point for the application.
- `pyproject.toml`: Project metadata and dependencies.

## Development Process
- Use README driven development, so the documentation is created and refined first, then after approval, the implementation begins.
- Happy Path tests should exist for all components, entry points and output methods. No need to write negative or boundary cases, but additional tests should be added to cover common risk areas.
