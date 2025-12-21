import configparser
from openai import OpenAI

class Session:
    def __init__(self, config: configparser.ConfigParser):
        self.config = config
        self.api_key = config["DEFAULT"].get("api_key")
        self.system_instruction = config["DEFAULT"].get("system_instruction")
        self.model = "gpt-4o"
        self.temperature = config["DEFAULT"].getfloat("temperature", 0.7)
        self.client = None

        if self.api_key:
            self.client = OpenAI(api_key=self.api_key)
