import configparser
import json
import os
import glob
from datetime import datetime
from openai import OpenAI
from file_context_loader import FileContextLoader
from tools import create_tool_registry

class Session:
    # Temperature presets
    TEMPERATURE_PRESETS = {
        "rigid": 0.2,
        "balanced": 0.7,
        "creative": 1.2
    }

    # Model presets organized by provider and capability
    MODEL_PRESETS = {
        "nano": "gpt-5-nano",
        "mini": "gpt-5-mini",
        "standard": "gpt-4o",
        "reasoning": "gpt-5.2"
    }

    # Personality presets are now loaded from config file (PERSONALITIES section)
    @staticmethod
    def load_personality_presets(config: configparser.ConfigParser) -> dict:
        if config.has_section("PERSONALITIES"):
            # Filter out keys inherited from [DEFAULT]
            return {
                key: value
                for key, value in config.items("PERSONALITIES")
                if key not in config.defaults()
            }
        # Fallback to hardcoded defaults if section missing
        return {
            "helpful": "You are a helpful and concise assistant. You enjoy helping the user with their requests.",
            "terse": "You are a laconic assistant that provides limited but correct responses. You have better things to do.",
            "detailed": "You are a helpful assistant that provides comprehensive, thorough responses. Include relevant details and explanations.",
            "creative": "You are an imaginative and creative collaborator. Use the prompt as inspiration to create and explore."
        }

    # Valid model names (for direct specification)
    VALID_MODELS = [
        "gpt-4o","gpt-5-nano", "gpt-5-mini", "gpt-4.1", "gpt-4.1-mini", "gpt-5.2", "gpt-5.2-mini", "gpt-3.5-turbo"
    ]

    def __init__(self, config: configparser.ConfigParser):
        self.config = config
        # Check for API key from environment variable first, then fall back to config file
        self.api_key = os.getenv("OPENAI_API_KEY") or config["DEFAULT"].get("api_key")
        self.personality_presets = self.load_personality_presets(config)
        self.personality = config["DEFAULT"].get("personality_preset", "helpful")
        self.system_instruction = self.personality_presets.get(self.personality, self.personality_presets["helpful"])
        model_preset = config["DEFAULT"].get("model_preset", "standard")
        self.model = self.MODEL_PRESETS.get(model_preset, model_preset)
        temp_value = config["DEFAULT"].get("temperature_preset", "balanced")
        self.temperature = self.TEMPERATURE_PRESETS.get(temp_value)
        if self.temperature is None:
            try:
                self.temperature = float(temp_value)
            except ValueError:
                self.temperature = self.TEMPERATURE_PRESETS["balanced"]
        self.max_history = config["DEFAULT"].getint("max_history", 100)
        self.log_truncate_len = config["DEFAULT"].getint("log_truncate_len", 20)
        self.file_context_max_size = config["DEFAULT"].getint("file_context_max_size", 50000)
        self.history = []
        self.client = None
        self.session_name = None
        self.sessions_dir = "sessions"
        self.file_context = FileContextLoader(max_size=self.file_context_max_size)
        self.tools = create_tool_registry()
        self.tools_enabled = config["DEFAULT"].getboolean("tools_enabled", True)
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

    def get_tool_schemas(self):
        """Get OpenAI function calling schemas for all tools."""
        if not self.tools_enabled:
            return []
        return [tool.to_schema() for tool in self.tools.values()]

    def execute_tool(self, tool_name: str, arguments: str):
        """
        Execute a tool by name with given arguments.

        Args:
            tool_name: Name of the tool to execute
            arguments: JSON string of arguments

        Returns:
            Tool execution result as string
        """
        if tool_name not in self.tools:
            return f"Error: Unknown tool '{tool_name}'"

        tool = self.tools[tool_name]
        return tool.execute(arguments)

    def list_tools(self):
        """List all available tools."""
        return list(self.tools.keys())

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

    def validate_options(self) -> list[str]:
        """
        Validate that current options are compatible with each other.
        Auto-corrects incompatible settings and returns list of adjustment messages.
        """
        adjustments = []

        # Rule: mini/nano models only support temperature of 1.0
        if "mini" in self.model or "nano" in self.model:
            if self.temperature != 1.0:
                old_temp = self.temperature
                self.temperature = 1.0
                adjustments.append(f"Temperature adjusted to 1.0 (was {old_temp}, {self.model} only supports temp=1.0)")

        return adjustments

    def set_temperature(self, value: str) -> tuple[float, str]:
        """
        Set temperature with validation and auto-correction.
        Returns: (actual_value, message)
        """
        # Check if it's a preset
        value_lower = value.lower()
        if value_lower in self.TEMPERATURE_PRESETS:
            self.temperature = self.TEMPERATURE_PRESETS[value_lower]
            return self.temperature, f"Temperature set to {self.temperature} ({value_lower})"

        # Try to parse as float
        try:
            temp = float(value)
            # Validate range
            if temp < 0.0 or temp > 2.0:
                # Auto-correct to nearest valid value
                corrected = max(0.0, min(2.0, temp))
                self.temperature = corrected
                return self.temperature, f"Temperature adjusted to {corrected} (was {temp}, valid range is 0.0-2.0)"
            self.temperature = temp
            return self.temperature, f"Temperature set to {temp}"
        except ValueError:
            # Try fuzzy matching with presets
            prefix_len = min(len(value_lower), 3)
            if prefix_len > 0:
                close_matches = [k for k in self.TEMPERATURE_PRESETS.keys() if k.startswith(value_lower[:prefix_len])]
                if close_matches:
                    suggestion = close_matches[0]
                    raise ValueError(f"Invalid temperature '{value}'. Did you mean '{suggestion}'? Valid presets: {', '.join(self.TEMPERATURE_PRESETS.keys())}")
            raise ValueError(f"Invalid temperature '{value}'. Use a number (0.0-2.0) or preset: {', '.join(self.TEMPERATURE_PRESETS.keys())}")

    def set_model(self, value: str) -> tuple[str, str]:
        """
        Set model with validation and auto-correction.
        Returns: (actual_value, message)
        """
        # Check if it's a preset
        value_lower = value.lower()
        if value_lower in self.MODEL_PRESETS:
            self.model = self.MODEL_PRESETS[value_lower]
            return self.model, f"Model set to {self.model}"

        # Accept direct model names (for flexibility)
        if value in self.VALID_MODELS:
            self.model = value
            return self.model, f"Model set to {value}"

        # Try fuzzy matching with presets
        prefix_len = min(len(value_lower), 3)
        if prefix_len > 0:
            close_matches = [k for k in self.MODEL_PRESETS.keys() if k.startswith(value_lower[:prefix_len])]
            if close_matches:
                suggestion = close_matches[0]
                raise ValueError(f"Unknown model '{value}'. Did you mean '{suggestion}'? Valid presets: {', '.join(self.MODEL_PRESETS.keys())}")
        raise ValueError(f"Unknown model '{value}'. Valid presets: {', '.join(self.MODEL_PRESETS.keys())} or use full model name")

    def set_personality(self, value: str) -> tuple[str, str]:
        """
        Set personality with validation and auto-correction.
        Returns: (actual_value, message)
        """
        value_lower = value.lower()
        if value_lower in self.personality_presets:
            self.personality = value_lower
            self.system_instruction = self.personality_presets[value_lower]
            return self.personality, f"Personality set to {value_lower}"

        # Try fuzzy matching with presets
        prefix_len = min(len(value_lower), 3)
        if prefix_len > 0:
            close_matches = [k for k in self.personality_presets.keys() if k.startswith(value_lower[:prefix_len])]
            if close_matches:
                suggestion = close_matches[0]
                raise ValueError(f"Unknown personality '{value}'. Did you mean '{suggestion}'? Valid options: {', '.join(self.personality_presets.keys())}")
        raise ValueError(f"Unknown personality '{value}'. Valid options: {', '.join(self.personality_presets.keys())}")
