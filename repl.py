import logging
import json
import sys
from importlib.metadata import version
from prompt_toolkit import PromptSession
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.styles import Style
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text
from session import Session

class Repl:
    def __init__(self, session: Session):
        self.session = session
        self.logger = logging.getLogger(__name__)
        self.prompt_session = PromptSession()
        self.console = Console()
        self.toolbar_style = Style.from_dict({
            'bottom-toolbar': 'bg:#333333 #888888',
        })
        self.commands = {
            "/version": self.cmd_version,
            "/help": self.cmd_help,
            "/exit": self.cmd_exit,
            "/quit": self.cmd_exit,
            "/save": self.cmd_save,
            "/load": self.cmd_load,
            "/history": self.cmd_history,
            "/set": self.cmd_set,
            "/add": self.cmd_add,
            "/remove": self.cmd_remove,
            "/context": self.cmd_context,
            "/refresh": self.cmd_refresh
        }

        # Print welcome banner
        self.console.print(Panel.fit(
            f"[bold blue]bChat[/bold blue] - AI Assistant\n"
            f"Model: [cyan]{self.session.model}[/cyan] | Temp: [cyan]{self.session.temperature}[/cyan]\n"
            f"Type [bold]/help[/bold] for commands.",
            title="Welcome",
            border_style="cyan"
        ))

    def get_prompt(self):
        return HTML(f"<style fg='#00ff00'>bChat</style> <style fg='#888888'>({self.session.model})</style> > ")

    def get_toolbar(self):
        session_name = self.session.session_name or "Unsaved"
        return HTML(f"<style bg='#333333' fg='#888888'> Session: {session_name} | Model: {self.session.model} | Temp: {self.session.temperature} </style>")

    def print_status(self, message: str, add_newline: bool = True):
        """Print a status message with visual continuity to panels. Always prefix with '|'."""
        # Remove any leading/trailing blank lines from message
        msg = message.strip('\n')
        # Add prefix to each line
        for line in msg.splitlines():
            self.console.print(f"[dim]│[/dim] {line}")
        if add_newline:
            self.console.print()

    def print_response(self, content: str):
        """Print AI response with left border for visual distinction."""
        # Render markdown with reduced width to account for "│ " prefix
        prefix_width = 3  # "│ " plus safety margin
        render_width = max(40, self.console.width - prefix_width)

        # Create a temporary console with the narrower width
        from io import StringIO
        temp_console = Console(
            file=StringIO(),
            width=render_width,
            force_terminal=True
        )
        temp_console.print(Markdown(content))
        rendered = temp_console.file.getvalue()

        # Add left border to each line using built-in print()
        # to avoid Rich re-processing the ANSI codes
        lines = rendered.rstrip().split('\n')
        for line in lines:
            print(f"\033[2m│\033[0m {line}")
        print()

    def run(self):
        while True:
            try:
                user_input = self.prompt_session.prompt(
                    self.get_prompt(),
                    bottom_toolbar=self.get_toolbar,
                    style=self.toolbar_style
                )
                self.handle_input(user_input)
            except KeyboardInterrupt:
                continue
            except EOFError:
                break
            except Exception as e:
                self.logger.error(f"Unexpected error in REPL loop: {e}", exc_info=True)
                self.console.print(f"[bold red]✖ Error:[/bold red] {e}")

    def handle_input(self, text: str):
        text = text.strip()
        if not text:
            return

        if text.startswith("/"):
            self.handle_command(text)
        else:
            self.handle_prompt(text)

    def handle_command(self, text: str):
        """
        Parse and execute commands with proper parameter handling.
        
        Parameter rules:
        - 0 params: /help, /exit, /quit, /version, /history, /context, /refresh
        - 1 param: /save, /load, /add, /remove - everything after command is the value
        - 2 params: /set - first token after command is param1, rest is param2
        """
        # Split command from rest of text
        parts = text.split(maxsplit=1)
        command = parts[0]
        remaining = parts[1] if len(parts) > 1 else ""
        
        if command not in self.commands:
            # Show yellow icon and 'unknown command' (no INFO word)
            valid_cmds = ', '.join(sorted(self.commands.keys()))
            self.print_status(f"[bold yellow]ℹ Unknown command:[/bold yellow] {command}", add_newline=False)
            self.print_status(f"[dim]Valid commands: {valid_cmds}[/dim]", add_newline=False)
            self.print_status(f"Type /help for usage.")
            return
        
        # Define parameter expectations for each command
        zero_param_commands = {"/help", "/exit", "/quit", "/version", "/history", "/context", "/refresh"}
        one_param_commands = {"/save", "/load", "/add", "/remove"}
        two_param_commands = {"/set"}

        # Helper for usage info
        def print_usage(cmd):
            if cmd in zero_param_commands:
                self.print_status(f"[bold yellow]ℹ Usage:[/bold yellow] {cmd}", add_newline=False)
            elif cmd in one_param_commands:
                self.print_status(f"[bold yellow]ℹ Usage:[/bold yellow] {cmd} <value>", add_newline=False)
            elif cmd == "/set":
                self.print_status(f"[bold yellow]ℹ Usage:[/bold yellow] /set <option> <value>", add_newline=False)
                self.print_status("[dim]Options: temp/temperature, model, personality[/dim]", add_newline=False)

        if command in zero_param_commands:
            if remaining:
                print_usage(command)
                return
            self.commands[command]([])
        elif command in one_param_commands:
            # /save and /load allow no-arg usage (auto-generate or load most recent)
            if command in {"/save", "/load"}:
                self.commands[command]([remaining] if remaining else [])
            else:
                if not remaining:
                    print_usage(command)
                    return
                self.commands[command]([remaining])
        elif command in two_param_commands:
            if not remaining:
                print_usage(command)
                return
            param_parts = remaining.split(maxsplit=1)
            if len(param_parts) < 2:
                print_usage(command)
                # If only option is provided, show valid options
                if param_parts:
                    opt = param_parts[0].lower()
                    valid_opts = ["temp", "temperature", "model", "personality"]
                    if opt not in valid_opts:
                        self.print_status(f"[bold yellow]ℹ Unknown option:[/bold yellow] '{opt}'", add_newline=False)
                        self.print_status(f"[dim]Valid options: temp/temperature, model, personality[/dim]", add_newline=False)
                return
            self.commands[command](param_parts)
        else:
            print_usage(command)
            return

    def handle_prompt(self, text: str):
        if not self.session.client:
            self.print_status("[bold red]✖ Error:[/bold red] OpenAI client not initialized (missing API key).")
            return

        try:
            self.session.add_message("user", text)
            messages = self.session.get_messages()

            # Log request with truncated prompt and estimated token size
            trunc_len = self.session.log_truncate_len
            truncated_prompt = (text[:trunc_len] + '..') if len(text) > trunc_len else text
            est_tokens = len(text) // 4
            self.logger.info(f"Request: {truncated_prompt} (Est. tokens: {est_tokens})")

            # Log full request at DEBUG level
            self.logger.debug(f"Full request messages: {json.dumps(messages)}")

            content = ""
            with self.console.status("[bold green]Thinking...[/bold green]", spinner="dots"):
                response = self.session.client.chat.completions.create(
                    model=self.session.model,
                    messages=messages,
                    temperature=self.session.temperature
                )
                content = response.choices[0].message.content

            self.print_response(content)

            self.session.add_message("assistant", content)

            # Log response with truncated content and token usage
            truncated_response = (content[:trunc_len] + '..') if len(content) > trunc_len else content
            total_tokens = response.usage.total_tokens if response.usage else "N/A"
            self.logger.info(f"Response: {truncated_response} (Tokens: {total_tokens})")

            self.logger.debug(f"Full response: {content}")

        except Exception as e:
            self.print_status(f"[bold red]✖ Error:[/bold red] {e}")
            self.logger.error(f"An error occurred: {e}", exc_info=True)

    def cmd_version(self, args):
        try:
            v = version("bchat")
            self.print_status(f"bchat version [bold]{v}[/bold]")
        except Exception:
            self.print_status("bchat version unknown")

    def cmd_help(self, args):
        help_text = """
[bold]Available commands:[/bold]

[bold yellow]General:[/bold yellow]
  [cyan]/version[/cyan]         - Display version
  [cyan]/help[/cyan]            - Show this help message
  [cyan]/exit[/cyan]            - Exit the application

[bold yellow]Sessions:[/bold yellow]
  [cyan]/save [name][/cyan]     - Save current session
  [cyan]/load [name][/cyan]     - Load a session
  [cyan]/history[/cyan]         - List saved sessions

[bold yellow]Configuration:[/bold yellow]
  [cyan]/set <option> <value>[/cyan] - Configure runtime settings
    Options: temp/temperature, model, personality
    Examples: /set temp 0.9, /set model gpt-mini

[bold yellow]File Context:[/bold yellow]
  [cyan]/add <file>[/cyan]      - Add file or glob pattern to context
  [cyan]/remove <file>[/cyan]   - Remove file from context
  [cyan]/context[/cyan]         - Show files and message history
  [cyan]/refresh[/cyan]         - Reload modified files
        """
        self.console.print(Panel(help_text.strip(), title="Help", border_style="green"))
        self.console.print()

    def cmd_save(self, args):
        name = args[0] if args else None
        try:
            saved_name = self.session.save_session(name)
            self.print_status(f"[bold green]✔ Saved:[/bold green] [cyan]{saved_name}[/cyan]")
        except Exception as e:
            self.print_status(f"[bold red]✖ Error:[/bold red] {e}")

    def cmd_load(self, args):
        name = args[0] if args else None
        try:
            loaded_name = self.session.load_session(name)
            self.print_status(f"[bold green]✔ Loaded:[/bold green] [cyan]{loaded_name}[/cyan] [dim](History: {len(self.session.history)} messages)[/dim]")
        except Exception as e:
            self.print_status(f"[bold red]✖ Error:[/bold red] {e}")

    def cmd_history(self, args):
        try:
            sessions = self.session.list_sessions()
            if not sessions:
                self.print_status("[yellow]No saved sessions found.[/yellow]")
                return

            text = Text()
            for s in sessions:
                text.append(f"{s['name']}", style="bold cyan")
                text.append(f" ({s['time'].strftime('%Y-%m-%d %H:%M:%S')})\n", style="dim")

            self.console.print(Panel(text, title="Saved Sessions", border_style="blue"))
            self.console.print()
        except Exception as e:
            self.print_status(f"[bold red]✖ Error:[/bold red] {e}")

    def cmd_set(self, args):
        """Set runtime configuration (temperature, model, personality)."""
        if len(args) < 2:
            self.print_status("[bold yellow]ℹ Usage:[/bold yellow] /set <option> <value>", add_newline=False)
            self.print_status("[dim]Options: temp/temperature, model, personality[/dim]", add_newline=False)
            return

        option = args[0].lower()
        value = args[1]

        try:
            if option in ["temp", "temperature"]:
                actual_value, message = self.session.set_temperature(value)
                self.print_status(f"[bold green]✔[/bold green] {message}")
            elif option == "model":
                actual_value, message = self.session.set_model(value)
                self.print_status(f"[bold green]✔[/bold green] {message}")
            elif option == "personality":
                actual_value, message = self.session.set_personality(value)
                self.print_status(f"[bold green]✔[/bold green] {message}")
            else:
                self.print_status(f"[bold yellow]ℹ Unknown option:[/bold yellow] '{option}'", add_newline=False)
                self.print_status("[dim]Valid options: temp/temperature, model, personality[/dim]", add_newline=False)
                return

            # Validate option compatibility and show any adjustments
            adjustments = self.session.validate_options()
            for adj in adjustments:
                self.print_status(f"[bold yellow]⚠[/bold yellow] {adj}")

        except ValueError as e:
            # Try to extract valid presets from the error message
            msg = str(e)
            # Always include 'Error:' for test compatibility
            if option in ["temp", "temperature"]:
                self.print_status(f"[bold red]✖ Error:[/bold red] {msg}")
                presets = ', '.join(self.session.TEMPERATURE_PRESETS.keys())
                self.print_status(f"[dim]Valid presets: {presets}[/dim]")
            elif option == "model":
                self.print_status(f"[bold red]✖ Error:[/bold red] {msg}")
                presets = ', '.join(self.session.MODEL_PRESETS.keys())
                self.print_status(f"[dim]Valid presets: {presets}[/dim]")
            elif option == "personality":
                self.print_status(f"[bold red]✖ Error:[/bold red] {msg}")
                presets = ', '.join(self.session.PERSONALITY_PRESETS.keys())
                self.print_status(f"[dim]Valid presets: {presets}[/dim]")
            else:
                self.print_status(f"[bold red]✖ Error:[/bold red] {msg}")

    def cmd_add(self, args):
        """Add file(s) to context. Supports glob patterns."""
        if not args:
            self.print_status("[bold red]✖ Error:[/bold red] Usage: /add <file or pattern>")
            return

        pattern = args[0]
        try:
            # Check if it's a glob pattern
            if '*' in pattern or '?' in pattern:
                contexts = self.session.file_context.add_glob(pattern)
                self.print_status(f"[bold green]✔ Added:[/bold green] {len(contexts)} file(s) matching '{pattern}'")
                for ctx in contexts:
                    self.console.print(f"[dim]│[/dim]   [cyan]{ctx.path}[/cyan] [dim]({ctx.line_count} lines)[/dim]")
                self.console.print()
            else:
                ctx = self.session.file_context.add_file(pattern)
                self.print_status(f"[bold green]✔ Added:[/bold green] [cyan]{ctx.path}[/cyan] [dim]({ctx.line_count} lines, {ctx.size} chars)[/dim]")
        except (FileNotFoundError, ValueError, PermissionError) as e:
            self.print_status(f"[bold red]✖ Error:[/bold red] {e}")

    def cmd_remove(self, args):
        """Remove file from context."""
        if not args:
            self.print_status("[bold red]✖ Error:[/bold red] Usage: /remove <file>")
            return

        path = args[0]
        if self.session.file_context.remove_file(path):
            self.print_status(f"[bold green]✔ Removed:[/bold green] [cyan]{path}[/cyan]")
        else:
            self.print_status(f"[bold yellow]⚠ Warning:[/bold yellow] File not in context: {path}")

    def cmd_context(self, args):
        """Display current context: loaded files and message history."""
        files = self.session.file_context.list_files()
        history = self.session.history

        # Build context display
        text = Text()

        # File context section
        text.append("Files:\n", style="bold yellow")
        if files:
            total_size = self.session.file_context.get_total_size()
            total_lines = self.session.file_context.get_total_lines()
            text.append(f"  {len(files)} file(s), {total_lines} lines, {total_size:,} chars\n", style="dim")
            for fc in files:
                text.append(f"  • {fc.path}\n", style="cyan")
        else:
            text.append("  No files loaded\n", style="dim")

        text.append("\n")

        # Message history section
        text.append("Messages:\n", style="bold yellow")
        if history:
            text.append(f"  {len(history)} message(s) in history\n", style="dim")
            # Show last few messages as preview
            preview_count = min(3, len(history))
            if preview_count > 0:
                for msg in history[-preview_count:]:
                    role = msg["role"]
                    content = msg["content"][:50] + ".." if len(msg["content"]) > 50 else msg["content"]
                    role_style = "green" if role == "user" else "blue"
                    text.append(f"  [{role}] ", style=role_style)
                    text.append(f"{content}\n", style="dim")
        else:
            text.append("  No messages in history\n", style="dim")

        self.console.print(Panel(text, title="Context", border_style="blue"))
        self.console.print()

    def cmd_refresh(self, args):
        """Reload files that have been modified."""
        updated = self.session.file_context.refresh()
        if updated:
            self.print_status(f"[bold green]✔ Refreshed:[/bold green] {len(updated)} file(s)")
            for path in updated:
                self.console.print(f"[dim]│[/dim]   [cyan]{path}[/cyan]")
            self.console.print()
        else:
            self.print_status("[dim]No files were modified.[/dim]")

    def cmd_exit(self, args):
        self.print_status("[bold cyan]Goodbye![/bold cyan]")
        sys.exit(0)
