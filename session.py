import configparser
from openai import OpenAI

class Session:
    def __init__(self, config: configparser.ConfigParser):
        self.config = config
        self.api_key = config["DEFAULT"].get("api_key")
        self.system_instruction = config["DEFAULT"].get("system_instruction")
        self.model = "gpt-4o"
        self.temperature = config["DEFAULT"].getfloat("temperature", 0.7)
        self.max_history = config["DEFAULT"].getint("max_history", 100)
        self.history = []
        self.client = None

        if self.api_key:
            self.client = OpenAI(api_key=self.api_key)

    def add_message(self, role: str, content: str):
        self.history.append({"role": role, "content": content})
        # Keep only the last max_history messages
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]

    def get_messages(self):
        messages = [{"role": "system", "content": self.system_instruction}]
        messages.extend(self.history)
        return messages
