# bchat

A command-line chatbot/REPL that interacts with OpenAI's GPT models. Designed for simplicity and extensibility to support future interfaces (web, GUI, etc.).

## Key Features

- **Interactive REPL**: Command-line interface with rich terminal UI and markdown rendering
- **Async/Await Architecture**: Non-blocking I/O operations using Python's asyncio for better responsiveness
- **Session Management**: Save and load conversation sessions asynchronously
- **Conversation History**: Maintain context across interactions with configurable history limits
- **File Context**: Load files into conversation context for AI-assisted code review and discussion
- **Tool Calling**: LLM can call tools like calculator, datetime, and shell commands to perform tasks
- **MCP Integration**: Connect to external MCP servers for additional tools (filesystem, GitHub, web fetching, custom tools)
- **Rich Terminal UI**: Beautiful output formatting with markdown support using the Rich library
- **Timeout Protection**: API calls and file operations protected with configurable timeouts
- **Robust Error Handling**: Graceful handling of network issues, file errors, and cancellation

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

**Command Parameter Rules:**
- **No parameters**: Commands like `/help`, `/exit`, `/quit`, `/version`, `/history`, `/info`, `/clear`, `/tools` take no parameters
- **Single parameter**: Commands like `/save` and `/load` treat everything after the command as a single value
  - Example: `/save my session name` saves with the name "my session name"
- **Two parameters**: Commands like `/set` split at the first space - first token is the option, rest is the value
  - Example: `/set temp 0.9` uses "temp" as option and "0.9" as value

#### Session Management
- `/version` - Display the application version
- `/help` - Show available commands
- `/info` - Display configuration and environment info
- `/save [name]` - Save current session (auto-generates name if not provided)
  - Example: `/save my important session` saves with name "my important session"
- `/load [name]` - Load a session (loads most recent if name not provided)
  - Example: `/load my important session` loads the session named "my important session"
- `/history` - List saved sessions with timestamps
- `/exit` or `/quit` - Exit the application

#### Runtime Configuration
- `/set <option> <value>` - Configure runtime settings (temperature, model, personality)

**Available Options:**
- `temp` or `temperature` - AI response randomness (0.0-2.0)
  - Presets: `default` (0.7), `rigid` (0.3), `creative` (1.5)
  - Examples: `/set temp creative`, `/set temperature 0.9`
- `model` - AI model to use
  - Presets:
    - `nano` (gpt-5-nano) - Smallest/fastest option
    - `mini` (gpt-5-mini) - Fast and economical
    - `standard` (gpt-4o) - Standard model
    - `reasoning` (gpt-5.2) - Deep reasoning model
  - Examples: `/set model mini`, `/set model standard`, `/set model reasoning`
  - Note: nano/mini models only support temperature=1.0 (auto-adjusted)
- `personality` - AI response style
  - Presets: Defined in `[PERSONALITIES]` section of `config.ini` (see below for example)
  - Examples: `/set personality terse`, `/set personality creative`


**Custom Personalities:**
You can add, remove, or edit personality presets in the `[PERSONALITIES]` section of your `config.ini` file. Example:

```ini
[PERSONALITIES]
helpful = You are a helpful and concise assistant. You enjoy helping the user with their requests.
terse = You are a laconic assistant that provides frank responses. You have better things to do.
detailed = You are a helpful assistant that provides comprehensive, thorough responses. Include relevant details and explanations.
creative = You are an imaginative and creative collaborator. Use the prompt as inspiration to create and explore.
```

**Auto-correction:** The system provides friendly suggestions when values are close to valid presets or ranges.

#### File Context & Session Clearing
- `/add <path|glob>` - Add file(s) to conversation context
- `/remove <path>` - Remove file from context
- `/context` - Show current context (loaded files and message history)
- `/refresh` - Reload file contents to detect changes
- `/clear` - Remove all messages and file context for a fresh start

**Clearing Context and History:**
Use `/clear` to empty both the current message history and file context. After running `/clear`, new prompts will not include any previous messages or loaded files. This is useful for starting a new topic or resetting the session without restarting the application.

#### Tools
- `/tools` - List available tools that the AI can use (calculator, datetime, shell commands)

### Tool Awareness and MCP Integration

bChat is designed to intelligently leverage both local tools and dynamic tools provided by MCP servers. This allows the AI to perform a wide range of tasks efficiently and contextually.

#### Local Tools
Local tools are built into the bChat application and are always available. These tools include:
- **calculator**: Perform mathematical calculations.
- **get_datetime**: Retrieve the current date and time.
- **shell_command**: Execute shell commands for file operations, system queries, etc.

To list all available local tools, use the `/tools` command:
```bash
/tools
```

#### MCP Server Tools
MCP servers extend the AI's capabilities by providing dynamic tools that can be connected and disconnected as needed. These tools are namespaced to avoid conflicts with local tools and are loaded dynamically when the server is connected.

**Examples of MCP Server Tools:**
- Filesystem operations (e.g., reading, writing, searching files)
- GitHub integration (e.g., managing repositories, issues, pull requests)
- Web fetching (e.g., HTTP requests, web scraping)

To view and manage MCP server tools, use the following commands:
- `/mcp status`: List all configured MCP servers and their connection state.
- `/mcp connect <server>`: Connect to a specific MCP server.
- `/mcp tools [server]`: List tools provided by a specific MCP server.

#### Encouraging Tool Usage
The AI is designed to:
1. **Prioritize Local Tools**: For tasks that can be handled efficiently with built-in tools, the AI will use local tools to minimize latency and complexity.
2. **Leverage MCP Tools Dynamically**: For advanced or external tasks, the AI will connect to MCP servers and use their tools as needed. This ensures that the AI can adapt to a wide range of scenarios without overloading the local environment.

**Configuration Example:**
To enable or disable tool usage, update the `config.ini` file:
```ini
[DEFAULT]
tools_enabled = True  # Set to False to disable local tool usage
mcp_autoconnect = True  # Automatically connect to MCP servers on startup
```

By combining local and MCP server tools, bChat provides a flexible and powerful environment for interacting with AI.

#### MCP Servers
- `/mcp status` - List all configured MCP servers and their connection state
- `/mcp connect <name>` - Connect to a specific MCP server from the configuration
- `/mcp disconnect <name>` - Disconnect from an MCP server
- `/mcp tools [server]` - List available MCP tools (optionally filtered by server name)
- `/mcp reload` - Reload MCP configuration and reconnect changed servers

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
bChat (gpt-4.1) > /add main.py session.py
│ ✔ Added: main.py (85 lines)
│ ✔ Added: session.py (82 lines)

bChat (gpt-4.1) > /context
┌─ Context ──────────────────────────────┐
│ Files:                                 │
│   main.py (85 lines, 2.4 KB)           │
│   session.py (82 lines, 3.0 KB)        │
│                                        │
│ Messages: 4 in history                 │
│ Total: 2 files, 167 lines, 5.4 KB      │
└────────────────────────────────────────┘
```

### Tool Calling Feature

The AI can use built-in tools to perform specific tasks like calculations, getting the current time, or executing shell commands. When you ask questions that require these capabilities, the AI will automatically call the appropriate tool.

**Available Tools:**
- **calculator**: Evaluate mathematical expressions
- **get_datetime**: Get current date/time with optional formatting
- **shell_command**: Execute shell commands

**List Tools:**
```bash
/tools                     # Display all available tools
```

**Example Usage:**
```
bChat (gpt-4o) > What's 123 * 456?
│ 🔧 Tool Call: calculator
│ ✔ Tool Result: 56088.0

The result of 123 × 456 is 56,088.

bChat (gpt-4o) > What time is it?
│ 🔧 Tool Call: get_datetime
│ ✔ Tool Result: 2025-12-25T03:45:30.123456

It's currently December 25, 2025 at 3:45 AM.

bChat (gpt-4o) > List files in the current directory
│ 🔧 Tool Call: shell_command
│ ✔ Tool Result: main.py
repl.py
session.py
tools.py
config.ini

Here are the files in the current directory:
- main.py
- repl.py
- session.py
- tools.py
- config.ini
```

**Configuration:**
Tools can be enabled/disabled in `config.ini`:
```ini
[DEFAULT]
tools_enabled = True    # Set to False to disable tool calling
```

### Model Context Protocol (MCP) Integration

bchat supports the Model Context Protocol (MCP), allowing you to connect to external MCP servers that provide additional tools and resources. MCP servers can extend the AI's capabilities beyond the built-in tools (calculator, datetime, shell commands).

**What is MCP?**
MCP is a standard protocol for connecting AI applications to external data sources and tools. MCP servers can provide access to:
- **Filesystem operations** (read, write, search files)
- **GitHub integration** (repositories, issues, PRs)
- **Web fetching** (HTTP requests, web scraping)
- **Database access** (SQL queries, data retrieval)
- **Custom tools** (any tool you or third parties build)

**Configuration:**
MCP servers are configured in `mcp_servers.yaml`:

```yaml
servers:
  # Filesystem server - Provides file operations
  filesystem:
    command: npx
    args: ["-y", "@modelcontextprotocol/server-filesystem", "~/projects"]
    autoconnect: true
    description: "Local filesystem operations"
    
  # GitHub server - Provides GitHub API operations
  github:
    command: npx
    args: ["-y", "@modelcontextprotocol/server-github"]
    env:
      GITHUB_TOKEN: ${GITHUB_TOKEN}
    autoconnect: false
    description: "GitHub repository and issue operations"
    
  # Fetch server - Provides web fetching capabilities
  fetch:
    command: npx
    args: ["-y", "@modelcontextprotocol/server-fetch"]
    autoconnect: true
    description: "HTTP fetch operations for web content"
```

**MCP Commands:**
- `/mcp status` - List all configured servers and their connection state
- `/mcp connect <name>` - Connect to a specific MCP server
- `/mcp disconnect <name>` - Disconnect from an MCP server
- `/mcp tools [server]` - List available MCP tools (optionally filter by server)
- `/mcp reload` - Reload configuration and reconnect changed servers

**Example Usage:**

*Viewing MCP Server Status:*
```
bChat (gpt-4o) > /mcp status
┌─ MCP Status ───────────────────────────────┐
│ MCP Servers:                               │
│                                            │
│ 🟢 filesystem [auto]                       │
│   Local filesystem operations              │
│   Tools: 5                                 │
│                                            │
│ ⚪ github [auto]                           │
│   GitHub repository operations             │
│   Not connected                            │
│                                            │
│ 🟢 fetch [auto]                            │
│   HTTP fetch operations                    │
│   Tools: 2                                 │
└────────────────────────────────────────────┘
```

*Connecting to a Server:*
```
bChat (gpt-4o) > /mcp connect github
│ Connecting to github...
│ ✔ Connected: github (12 tools available)
```

*Listing MCP Tools:*
```
bChat (gpt-4o) > /mcp tools github
┌─ MCP Tools ────────────────────────────────┐
│ Tools from github:                         │
│                                            │
│ [github]                                   │
│   • mcp_github_list_repos                  │
│     List repositories for a user or org    │
│   • mcp_github_get_issue                   │
│     Get details of a specific issue        │
│   • mcp_github_create_issue                │
│     Create a new issue                     │
└────────────────────────────────────────────┘
```

*Using MCP Tools (Automatically):*
```
bChat (gpt-4o) > Read the contents of README.md
│ 🔧 Tool Call: mcp_filesystem_read_file
│ ✔ Tool Result: # bchat
A command-line chatbot that interacts with OpenAI...

Here's what's in your README.md file:
[AI summarizes the contents]
```

**Tool Namespacing:**
MCP tools are automatically namespaced to avoid conflicts with local tools:
- Local tools: `calculator`, `get_datetime`, `shell_command`
- MCP tools: `mcp_{server}_{tool}` (e.g., `mcp_github_list_repos`)

**Auto-Connect:**
Servers with `autoconnect: true` will be automatically connected when bchat starts. Servers with `autoconnect: false` must be manually connected using `/mcp connect <name>`.

**Hot-Swapping:**
You can connect and disconnect servers without restarting bchat. Use `/mcp reload` to re-read the configuration file and automatically reconnect any changed servers.

**Installing MCP Servers:**
Most MCP servers are available via npm. The examples above use `npx` to run servers without installing them globally, but you can also install them:

```bash
# Install filesystem server globally
npm install -g @modelcontextprotocol/server-filesystem

# Install GitHub server globally
npm install -g @modelcontextprotocol/server-github

# Install fetch server globally
npm install -g @modelcontextprotocol/server-fetch
```

**Custom MCP Servers:**
You can create your own MCP servers or use community-built servers. See the [MCP documentation](https://modelcontextprotocol.io) for details on building custom servers.

### Runtime Configuration Feature

Adjust AI behavior during a conversation without restarting the application.

**Changing Temperature:**
```bash
/set temp 0.9              # Numeric value between 0.0 and 2.0
/set temperature creative  # Use preset (rigid/balanced/creative)
```

**Changing Model:**
```bash
/set model nano            # Use smallest/fastest model (gpt-5-nano)
/set model mini            # Use fast/economical model (gpt-5-mini)
/set model standard        # Use standard model (gpt-4o)
/set model reasoning       # Use deep reasoning model (gpt-5.2)
/set model gpt-4.1         # Use model name directly
```

**Changing Personality:**
```bash
/set personality terse     # Laconic, limited responses
/set personality detailed  # Comprehensive, thorough responses
/set personality creative  # Imaginative collaborator
```

**Example:**
```
bChat (gpt-4.1) > /set temperature creative
│ ✔ Temperature set to 1.5 (creative)

bChat (gpt-4.1) > /set model mini
│ ✔ Model set to gpt-5-mini-2025-08-07
│ ⚠ Temperature adjusted to 1.0 (was 1.5, gpt-5-mini-2025-08-07 only supports temp=1.0)

bChat (gpt-5-mini-2025-08-07) > /set personality detailed
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
- `tools_enabled`: Enable/disable tool calling functionality (default: True)

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
- `file_context_loader.py` - File context loading and management
- `tools.py` - Tool definitions and execution for LLM function calling
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

- **main.py**: Application entry point. Uses `asyncio.run()` to manage the async event loop. Loads configuration from `config.ini` and `secrets.ini`, initializes logging, creates `Session` and `Repl` instances, and starts the REPL loop. Ensures proper cleanup of async resources (AsyncOpenAI client) on shutdown.

- **session.py**: Manages application state independent of UI. Uses `AsyncOpenAI` client for non-blocking API calls. Handles conversation history (rolling window with max_history limit), tool registry, and session persistence (async save/load to JSON files in `sessions/` directory using `asyncio.to_thread()`).

- **repl.py**: Handles all user interaction asynchronously. Uses `asyncio.to_thread()` to run blocking `prompt_toolkit` input in a thread pool. Uses `Rich` for output (panels, markdown rendering, status messages). Manages tool call display and execution flow with timeout protection on API calls.

- **file_context_loader.py**: Manages file contexts for injection into AI conversations. All file I/O operations (reads, stat calls, glob) use `asyncio.to_thread()` to avoid blocking the event loop. Handles file loading, glob patterns, size limits, and content refresh.

- **tools.py**: Defines callable tools that the LLM can use via OpenAI's function calling API. Each tool has a schema, description, and execution function. Includes calculator, datetime, and shell command tools. Currently synchronous but called from async context.

### Async Architecture

The application uses Python's `asyncio` for non-blocking I/O operations:

**Async Patterns Used:**
- `asyncio.run()` - Top-level entry point managing the event loop lifecycle
- `async def` / `await` - All I/O-bound operations are async (API calls, file operations)
- `asyncio.to_thread()` - Offloads blocking operations to thread pool (file I/O, prompt_toolkit input)
- `asyncio.wait_for()` - Timeout protection on API calls (60 second default)
- `AsyncOpenAI` - Non-blocking OpenAI API client

**Threading Model:**
- Main event loop runs in the main thread
- Blocking I/O (file reads/writes, prompt input) executed in thread pool via `asyncio.to_thread()`
- Thread pool size managed automatically by asyncio (default: min(32, CPU_COUNT + 4))

### Data Flow

```
User Input → asyncio.to_thread(prompt_toolkit.prompt()) [Thread Pool]
          ↓
     Repl.handle_input() [Async]
          ↓
     Session.add_message() [Sync - fast]
          ↓
     Session.get_messages() [Sync - fast]
          ↓
     FileContextLoader.format_for_prompt() [Sync - fast]
          ↓
     await AsyncOpenAI.chat.completions.create() [Async - Network I/O]
          ↓ (with timeout protection)
     Tool calls? (if requested by LLM)
          ├─ Session.execute_tool() [Sync - fast]
          └─ await AsyncOpenAI.chat.completions.create() [Async - Network I/O]
          ↓
     Repl.print_response() [Sync - fast]
```

**Key Async Points:**
1. **User Input**: Blocking prompt_toolkit runs in thread pool
2. **API Calls**: All OpenAI requests are async with 60s timeout
3. **File Operations**: All file I/O uses thread pool (read, write, stat, glob)
4. **Session Save/Load**: JSON serialization runs in thread pool

### UI Library Integration

The application uses two terminal libraries that must be kept separate:

- **prompt_toolkit**: Handles input prompt and bottom toolbar. Uses `HTML` markup and `Style` objects. Blocking operation wrapped with `asyncio.to_thread()`.
- **Rich**: Handles all output (panels, markdown, status messages). Uses Rich markup syntax. Non-blocking (fast synchronous rendering).

**Important**: Do not pass Rich-rendered ANSI output through Rich's `console.print()` again—this causes double-processing. When combining pre-rendered content with prefixes, use Python's built-in `print()` with raw ANSI codes.

### Session Storage

Sessions are stored as JSON files in the `sessions/` directory:
```json
[
  {"role": "user", "content": "Hello"},
  {"role": "assistant", "content": "Hi there!"}
]
```

File operations use `asyncio.to_thread()` for non-blocking I/O.

## Logging

The application logs events to a file specified in the configuration (default: `bchat.log`).

**Log Levels:**
- **INFO**: High-level events including startup, shutdown, truncated user prompts, API responses with token counts
- **DEBUG**: Detailed information including full API request payloads, full API responses, async operation details, thread pool usage
- **ERROR**: Error details when exceptions occur, including full stack traces

**Async-Related Logging:**
- REPL loop lifecycle (start, cancellation, errors)
- AsyncOpenAI client initialization and cleanup
- File I/O operations (save/load timing)
- API call timeouts and retries
- Thread pool offloading for blocking operations

**Log Format:**
`%(asctime)s - %(name)s - %(levelname)s - %(message)s`

## Future Development Considerations

### Async Extensions

The async architecture provides a foundation for future enhancements:

**Potential Async Integrations:**
- **Streaming Responses**: OpenAI supports streaming completions - can be integrated with minimal changes
- **Concurrent Tool Execution**: Tools can be executed in parallel using `asyncio.gather()` when independent
- **WebSocket Support**: Real-time updates and notifications without blocking
- **Background Tasks**: Periodic session autosave, file watching, or health checks
- **Multi-User Support**: Handle multiple concurrent sessions in server mode

**Performance Optimizations:**
- Replace `asyncio.to_thread()` with true async libraries where available (e.g., `aiofiles` for file I/O)
- Implement connection pooling for API requests
- Add caching layer for repeated API calls
- Consider concurrent file loading in `add_glob()` using `asyncio.gather()`

**Error Handling Improvements:**
- Implement exponential backoff for API retries
- Add circuit breaker pattern for API failures
- Implement request queuing with rate limiting
- Add health check endpoint for monitoring

### Known Limitations

1. **Thread Pool Exhaustion**: Heavy concurrent file operations could exhaust the thread pool. Current default (min(32, CPU_COUNT + 4)) is adequate for typical CLI usage but may need tuning for server deployment.

2. **Tool Execution Blocking**: Shell commands and other tools execute synchronously in the async context. Long-running shell commands will block tool execution loop (but not the REPL). Consider moving to `asyncio.to_thread()` if tools become slow.

3. **No Connection Pooling**: AsyncOpenAI client creates new connections for each request. For high-volume usage, implement connection pooling.

4. **File Context Race Conditions**: Concurrent modifications to session history (e.g., from multiple coroutines) are not protected. Current single-REPL design prevents this, but multi-session server would need locking.

5. **Cancellation Propagation**: While `CancelledError` is caught in the REPL loop, not all async operations properly propagate cancellation. Background tasks should use `asyncio.create_task()` with proper cancellation handling.

## Debugging Tips

### Async Debugging

**Enable Debug Logging:**
```ini
# In config.ini
log_level = DEBUG
```

This logs:
- Full API request/response payloads
- Thread pool offloading operations
- Async operation timing
- File I/O operations

**Check for Blocking Operations:**
```python
# Set asyncio debug mode (add to main.py temporarily)
import asyncio
asyncio.get_event_loop().set_debug(True)
```

This warns about:
- Coroutines that take >100ms (adjust with `slow_callback_duration`)
- Blocking operations in async context
- Unawaited coroutines

**Monitor Event Loop:**
```python
# Add instrumentation to main.py
import logging
logging.getLogger('asyncio').setLevel(logging.DEBUG)
```

**Common Async Issues:**

1. **"coroutine was never awaited"**: Missing `await` keyword before async call
   ```python
   # Wrong:
   session.save_session("name")
   
   # Correct:
   await session.save_session("name")
   ```

2. **Timeout Errors**: API calls timing out (60s default)
   - Check network connectivity
   - Verify API key is valid
   - Check OpenAI service status
   - Increase timeout if needed (modify `asyncio.wait_for()` calls)

3. **Thread Pool Exhaustion**: Too many concurrent blocking operations
   - Reduce concurrent file operations
   - Check for leaked threads (threads not completing)
   - Monitor with: `asyncio.get_running_loop().get_debug()`

4. **Cancelled Errors**: Task cancelled during execution
   - Usually from Ctrl+C or timeout
   - Check finally blocks execute for cleanup
   - Ensure `CancelledError` is propagated, not caught

**Profiling Async Code:**
```bash
# Run with asyncio profiling
python -X dev -m main

# Or use py-spy for live profiling
py-spy record --native -o profile.svg -- python -m main
```

**Testing Async Code:**
```python
# Use pytest-asyncio for async tests
@pytest.mark.asyncio
async def test_my_async_function():
    result = await my_async_function()
    assert result == expected
```

**Debugging API Issues:**
- Set `log_level = DEBUG` to see full request/response
- Check `bchat.log` for detailed error messages
- Verify API key: `echo $OPENAI_API_KEY` or check `secrets.ini`
- Test API key with curl:
  ```bash
  curl https://api.openai.com/v1/models \
    -H "Authorization: Bearer $OPENAI_API_KEY"
  ```

**Debugging File Operations:**
- Enable DEBUG logging to see file I/O timing
- Check file permissions: `ls -l path/to/file`
- Verify file encoding: `file path/to/file`
- Test file reads manually:
  ```python
  import asyncio
  from file_context_loader import FileContextLoader
  
  async def test():
      loader = FileContextLoader()
      ctx = await loader.add_file("path/to/file")
      print(ctx)
  
  asyncio.run(test())
  ```

**Log Format:**
`%(asctime)s - %(name)s - %(levelname)s - %(message)s`
