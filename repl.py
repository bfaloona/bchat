import logging
import json
import sys
from importlib.metadata import version
from prompt_toolkit import PromptSession
from prompt_toolkit.formatted_text import HTML
from session import Session

class Repl:
    def __init__(self, session: Session):
        self.session = session
        self.logger = logging.getLogger(__name__)
        self.prompt_session = PromptSession()
        self.commands = {
            "/version": self.cmd_version,
            "/help": self.cmd_help,
            "/exit": self.cmd_exit,
            "/quit": self.cmd_exit
        }

    def get_prompt(self):
        return HTML(f"<b>== {self.session.model} / {self.session.temperature} ==</b>\n<b>bChat&gt;</b> ")

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
                print(f"Error: {e}")

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
            print(f"Unknown command: {command}")

    def handle_prompt(self, text: str):
        if not self.session.client:
            print("Error: OpenAI client not initialized (missing API key).")
            return

        try:
            print("Sending request to OpenAI...")
            self.logger.info("Sending request to OpenAI...")
            
            messages = [
                {"role": "system", "content": self.session.system_instruction},
                {"role": "user", "content": text}
            ]
            
            # Log truncated user prompt at INFO level
            truncated_content = (text[:20] + '..') if len(text) > 20 else text
            self.logger.info(f"User prompt: {truncated_content}")
            
            # Log full request at DEBUG level
            self.logger.debug(f"Full request messages: {json.dumps(messages)}")

            response = self.session.client.chat.completions.create(
                model=self.session.model,
                messages=messages,
                temperature=self.session.temperature
            )
            
            content = response.choices[0].message.content
            print(content)
            
            self.logger.info("Received response from OpenAI")
            self.logger.debug(f"Full response: {content}")
            
        except Exception as e:
            print(f"An error occurred: {e}")
            self.logger.error(f"An error occurred: {e}", exc_info=True)

    def cmd_version(self, args):
        try:
            v = version("bchat")
            print(f"bchat version {v}")
        except Exception:
            print("bchat version unknown")

    def cmd_help(self, args):
        print("Available commands:")
        print("  /version - Display version")
        print("  /help    - Show this help message")
        print("  /exit    - Exit the application")

    def cmd_exit(self, args):
        print("Goodbye!")
        sys.exit(0)
