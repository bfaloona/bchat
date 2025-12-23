import configparser
import json
import os
import glob
from datetime import datetime
from openai import OpenAI
from file_context_loader import FileContextLoader

class Session:
    def __init__(self, config: configparser.ConfigParser):
        self.config = config
        # Check for API key from environment variable first, then fall back to config file
        self.api_key = os.getenv("OPENAI_API_KEY") or config["DEFAULT"].get("api_key")
        self.system_instruction = config["DEFAULT"].get("system_instruction")
        self.model = "gpt-4o"
        self.temperature = config["DEFAULT"].getfloat("temperature", 0.7)
        self.max_history = config["DEFAULT"].getint("max_history", 100)
        self.log_truncate_len = config["DEFAULT"].getint("log_truncate_len", 20)
        self.file_context_max_size = config["DEFAULT"].getint("file_context_max_size", 50000)
        self.history = []
        self.client = None
        self.session_name = None
        self.sessions_dir = "sessions"
        self.file_context = FileContextLoader(max_size=self.file_context_max_size)
        os.makedirs(self.sessions_dir, exist_ok=True)

        if self.api_key:
            self.client = OpenAI(api_key=self.api_key)

    def add_message(self, role: str, content: str):
        self.history.append({"role": role, "content": content})
        # Keep only the last max_history messages
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]

    def get_messages(self):
        """Build messages list with system prompt, file context, and history."""
        # Start with system instruction
        system_content = self.system_instruction

        # Add file context if any files are loaded
        file_context_str = self.file_context.format_for_prompt()
        if file_context_str:
            system_content += "\n\n## File Context\n" + file_context_str

        messages = [{"role": "system", "content": system_content}]
        messages.extend(self.history)
        return messages

    def save_session(self, name: str = None):
        if name:
            self.session_name = name

        if not self.session_name:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.session_name = f"session_{timestamp}"

        file_path = os.path.join(self.sessions_dir, f"{self.session_name}.json")

        with open(file_path, 'w') as f:
            json.dump(self.history, f, indent=2)

        return self.session_name

    def load_session(self, name: str = None):
        if not name:
            # Find most recent
            files = glob.glob(os.path.join(self.sessions_dir, "*.json"))
            if not files:
                raise FileNotFoundError("No saved sessions found.")
            file_path = max(files, key=os.path.getmtime)
            name = os.path.splitext(os.path.basename(file_path))[0]
        else:
            file_path = os.path.join(self.sessions_dir, f"{name}.json")
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Session '{name}' not found.")

        with open(file_path, 'r') as f:
            self.history = json.load(f)

        self.session_name = name
        return self.session_name

    def list_sessions(self):
        files = glob.glob(os.path.join(self.sessions_dir, "*.json"))
        sessions = []
        for f in files:
            name = os.path.splitext(os.path.basename(f))[0]
            mod_time = datetime.fromtimestamp(os.path.getmtime(f))
            sessions.append({"name": name, "time": mod_time})

        # Sort by time descending
        sessions.sort(key=lambda x: x["time"], reverse=True)
        return sessions
