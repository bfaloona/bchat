# Copilot Instructions for bchat

## Project Overview
This is a simple chatbot Python project named `bchat`. Currently implemented as a command-line REPL, the architecture must allow easy extension to other interfaces (e.g., web, GUI) in the future.

## Tech Stack
- **Language**: Python 3.13+
- **Build System**: pyproject.toml (setuptools)
- **Testing**: pytest and GitHub Actions
- **AI Provider**: OpenAI API
- **Configuration**: config.ini (settings), secrets.ini (API keys, gitignored)
- **UI Libraries**: Rich (terminal formatting), prompt_toolkit (REPL input)

## Project Structure
- `main.py`: Entry point, logging setup, config loading.
- `session.py`: Session state, OpenAI client, history management.
- `repl.py`: REPL loop, commands, user interaction.
- `sessions/`: Saved chat session JSON files.
- `scripts/`: Build and test scripts.
- `tests/`: pytest test files.

## Coding Standards
- Use PEP 8 formatting.
- Prefer `pathlib` over `os.path`.
- Use type hints for function arguments and return values.
- Docstrings should follow the Google Python Style Guide.
- Ensure no whitespace on blank lines.
- Ensure no trailing whitespace at the end of lines.
- When mixing Rich and prompt_toolkit, be aware of ANSI code conflicts.

## Development Process

### README-Driven Development
Before implementing a feature:
1. **Define requirements** - Document what the feature does from the user's perspective in README.md (usage, commands, examples).
2. **Define architecture** - Document technical approach in README.md's "Architecture" section if the change affects component design, data flow, or introduces new dependencies.
3. **Review** - Get approval on README changes before writing code.
4. **Implement** - Code to match the documented behavior.

This ensures requirements are clear, architecture is intentional, and documentation stays current.

### Testing
Happy path tests should exist for all components, entry points, and output methods. Additional tests should cover common risk areas.

## Agent Workflow
1. **Gather context** before editing. Read relevant files first.
2. **Ask clarifying questions** if requirements are ambiguous.
3. **Follow README-Driven Development** for significant changes.
4. **Verify changes** by running `./scripts/test.sh` or the application.
5. **Self-correct errors** before reporting completion.
