import logging
import json
import sys
from importlib.metadata import version
from prompt_toolkit import PromptSession
from prompt_toolkit.formatted_text import HTML
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
        self.commands = {
            "/version": self.cmd_version,
            "/help": self.cmd_help,
            "/exit": self.cmd_exit,
            "/quit": self.cmd_exit,
            "/save": self.cmd_save,
            "/load": self.cmd_load,
            "/history": self.cmd_history
        }

        # Print welcome banner
        self.console.print(Panel.fit(
            f"[bold blue]bChat[/bold blue] - AI Assistant\n"
            f"Model: [cyan]{self.session.model}[/cyan] | Temp: [cyan]{self.session.temperature}[/cyan]\n"
            f"Type [bold]/help[/bold] for commands.",
            title="Welcome",
            border_style="blue"
        ))

    def get_prompt(self):
        return HTML(f"<style fg='#00ff00'>bChat</style> <style fg='#888888'>({self.session.model})</style> > ")

    def run(self):
        while True:
            try:
                user_input = self.prompt_session.prompt(self.get_prompt())
                self.handle_input(user_input)
            except KeyboardInterrupt:
                continue
            except EOFError:
                break
            except Exception as e:
                self.logger.error(f"Unexpected error in REPL loop: {e}", exc_info=True)
                self.console.print(f"[bold red]Error:[/bold red] {e}")

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
            self.console.print(f"[bold red]Unknown command:[/bold red] {command}")

    def handle_prompt(self, text: str):
        if not self.session.client:
            self.console.print("[bold red]Error:[/bold red] OpenAI client not initialized (missing API key).")
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

            self.console.print(Markdown(content))
            self.console.print() # Add a newline

            self.session.add_message("assistant", content)

            # Log response with truncated content and token usage
            truncated_response = (content[:trunc_len] + '..') if len(content) > trunc_len else content
            total_tokens = response.usage.total_tokens if response.usage else "N/A"
            self.logger.info(f"Response: {truncated_response} (Tokens: {total_tokens})")

            self.logger.debug(f"Full response: {content}")

        except Exception as e:
            self.console.print(f"[bold red]An error occurred:[/bold red] {e}")
            self.logger.error(f"An error occurred: {e}", exc_info=True)

    def cmd_version(self, args):
        try:
            v = version("bchat")
            self.console.print(f"bchat version [bold]{v}[/bold]")
        except Exception:
            self.console.print("bchat version unknown")

    def cmd_help(self, args):
        help_text = """
[bold]Available commands:[/bold]
  [cyan]/version[/cyan]     - Display version
  [cyan]/help[/cyan]        - Show this help message
  [cyan]/exit[/cyan]        - Exit the application
  [cyan]/save [name][/cyan] - Save current session
  [cyan]/load [name][/cyan] - Load a session
  [cyan]/history[/cyan]     - List saved sessions
        """
        self.console.print(Panel(help_text.strip(), title="Help", border_style="green"))

    def cmd_save(self, args):
        name = args[0] if args else None
        try:
            saved_name = self.session.save_session(name)
            self.console.print(f"[green]Session saved as:[/green] [bold]{saved_name}[/bold]")
        except Exception as e:
            self.console.print(f"[bold red]Error saving session:[/bold red] {e}")

    def cmd_load(self, args):
        name = args[0] if args else None
        try:
            loaded_name = self.session.load_session(name)
            self.console.print(f"[green]Session loaded:[/green] [bold]{loaded_name}[/bold]")
            self.console.print(f"[dim]History length: {len(self.session.history)} messages[/dim]")
        except Exception as e:
            self.console.print(f"[bold red]Error loading session:[/bold red] {e}")

    def cmd_history(self, args):
        try:
            sessions = self.session.list_sessions()
            if not sessions:
                self.console.print("[yellow]No saved sessions found.[/yellow]")
                return

            text = Text()
            for s in sessions:
                text.append(f"{s['name']}", style="bold cyan")
                text.append(f" ({s['time'].strftime('%Y-%m-%d %H:%M:%S')})\n", style="dim")

            self.console.print(Panel(text, title="Saved Sessions", border_style="blue"))
        except Exception as e:
            self.console.print(f"[bold red]Error listing sessions:[/bold red] {e}")

    def cmd_exit(self, args):
        self.console.print("[bold blue]Goodbye![/bold blue]")
        sys.exit(0)
