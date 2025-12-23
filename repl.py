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

    def print_status(self, message: str):
        """Print a status message with visual continuity to panels."""
        self.console.print(f"[dim]│[/dim] {message}")
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
        parts = text.split()
        command = parts[0]

        if command in self.commands:
            self.commands[command](parts[1:])
        else:
            self.print_status(f"[bold red]✖ Unknown command:[/bold red] {command}")

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
  [cyan]/version[/cyan]     - Display version
  [cyan]/help[/cyan]        - Show this help message
  [cyan]/exit[/cyan]        - Exit the application
  [cyan]/save [name][/cyan] - Save current session
  [cyan]/load [name][/cyan] - Load a session
  [cyan]/history[/cyan]     - List saved sessions
  [cyan]/add <path>[/cyan]  - Add file(s) to context (supports glob patterns)
  [cyan]/remove <path>[/cyan] - Remove file from context
  [cyan]/context[/cyan]     - List loaded files
  [cyan]/refresh[/cyan]     - Refresh file contents
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

    def cmd_exit(self, args):
        self.print_status("[bold cyan]Goodbye![/bold cyan]")
        sys.exit(0)

    def cmd_add(self, args):
        if not args:
            self.print_status("[bold red]✖ Error:[/bold red] No path specified. Usage: /add <path>")
            return

        path_pattern = " ".join(args)

        # Check if it's a glob pattern
        if '*' in path_pattern or '?' in path_pattern:
            added = self.session.context_loader.add_glob(path_pattern)
            if added:
                self.print_status(f"[bold green]✔ Added:[/bold green] {len(added)} file(s) matching {path_pattern}")
                for fc in added[:5]:  # Show first 5
                    self.print_status(f"  [dim]•[/dim] {fc}")
                if len(added) > 5:
                    self.print_status(f"  [dim]... and {len(added) - 5} more[/dim]")
            else:
                self.print_status(f"[bold yellow]⚠ Warning:[/bold yellow] No files found matching {path_pattern}")
        else:
            fc = self.session.context_loader.add_file(path_pattern)
            if fc:
                self.print_status(f"[bold green]✔ Added:[/bold green] {fc}")
            else:
                self.print_status(f"[bold red]✖ Error:[/bold red] Could not add file {path_pattern} (not found or too large)")

    def cmd_remove(self, args):
        if not args:
            self.print_status("[bold red]✖ Error:[/bold red] No path specified. Usage: /remove <path>")
            return

        path = " ".join(args)
        if self.session.context_loader.remove_file(path):
            self.print_status(f"[bold green]✔ Removed:[/bold green] {path}")
        else:
            self.print_status(f"[bold red]✖ Error:[/bold red] File not found in context: {path}")

    def cmd_context(self, args):
        files = self.session.context_loader.list_files()

        if not files:
            self.print_status("[yellow]No files loaded in context.[/yellow]")
            return

        text = Text()
        for fc in files:
            text.append(f"{fc}\n", style="cyan")

        total_size = self.session.context_loader.get_total_size() / 1024
        text.append(f"\nTotal: {len(files)} file(s), {total_size:.1f} KB", style="bold")

        self.console.print(Panel(text, title="Loaded Files", border_style="blue"))
        self.console.print()

    def cmd_refresh(self, args):
        updated = self.session.context_loader.refresh()

        if updated:
            self.print_status(f"[bold green]✔ Updated:[/bold green] {len(updated)} file(s)")
            for path in updated[:5]:
                self.print_status(f"  [dim]•[/dim] {path}")
            if len(updated) > 5:
                self.print_status(f"  [dim]... and {len(updated) - 5} more[/dim]")
        else:
            self.print_status("[dim]No files were updated.[/dim]")
