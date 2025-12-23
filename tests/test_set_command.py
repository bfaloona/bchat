import configparser
import pytest
from session import Session
from repl import Repl

def test_session_default_model():
    """Test that the default model is set to Claude Sonnet."""
    mock_config = configparser.ConfigParser()
    mock_config["DEFAULT"] = {"api_key": "test-key"}
    session = Session(mock_config)

    # Verify the default model is Claude Sonnet
    assert session.model == "claude-3-5-sonnet-20241022"


def test_set_temperature_numeric():
    """Test setting temperature with numeric value."""
    mock_config = configparser.ConfigParser()
    mock_config["DEFAULT"] = {"api_key": "test-key"}
    session = Session(mock_config)

    # Test valid numeric value
    value, message = session.set_temperature("0.9")
    assert value == 0.9
    assert session.temperature == 0.9
    assert "0.9" in message


def test_set_temperature_preset():
    """Test setting temperature with preset values."""
    mock_config = configparser.ConfigParser()
    mock_config["DEFAULT"] = {"api_key": "test-key"}
    session = Session(mock_config)

    # Test rigid preset
    value, message = session.set_temperature("rigid")
    assert value == 0.3
    assert session.temperature == 0.3
    assert "rigid" in message

    # Test creative preset
    value, message = session.set_temperature("creative")
    assert value == 1.5
    assert session.temperature == 1.5
    assert "creative" in message


def test_set_temperature_out_of_range():
    """Test temperature auto-correction for out-of-range values."""
    mock_config = configparser.ConfigParser()
    mock_config["DEFAULT"] = {"api_key": "test-key"}
    session = Session(mock_config)

    # Test value too high
    value, message = session.set_temperature("3.0")
    assert value == 2.0
    assert session.temperature == 2.0
    assert "adjusted" in message.lower()

    # Test value too low
    value, message = session.set_temperature("-0.5")
    assert value == 0.0
    assert session.temperature == 0.0
    assert "adjusted" in message.lower()


def test_set_temperature_invalid():
    """Test invalid temperature values."""
    mock_config = configparser.ConfigParser()
    mock_config["DEFAULT"] = {"api_key": "test-key"}
    session = Session(mock_config)

    # Test invalid string
    with pytest.raises(ValueError) as exc_info:
        session.set_temperature("invalid")
    assert "Invalid temperature" in str(exc_info.value)


def test_set_model_preset():
    """Test setting model with preset values."""
    mock_config = configparser.ConfigParser()
    mock_config["DEFAULT"] = {"api_key": "test-key"}
    session = Session(mock_config)

    # Test mini preset
    value, message = session.set_model("mini")
    assert value == "claude-3-5-haiku-20241022"
    assert session.model == "claude-3-5-haiku-20241022"
    assert "claude-3-5-haiku-20241022" in message


def test_set_model_direct():
    """Test setting model with direct model name."""
    mock_config = configparser.ConfigParser()
    mock_config["DEFAULT"] = {"api_key": "test-key"}
    session = Session(mock_config)

    # Test direct model name
    value, message = session.set_model("gpt-4o-mini")
    assert value == "gpt-4o-mini"
    assert session.model == "gpt-4o-mini"


def test_set_model_invalid():
    """Test invalid model values."""
    mock_config = configparser.ConfigParser()
    mock_config["DEFAULT"] = {"api_key": "test-key"}
    session = Session(mock_config)

    # Test invalid model
    with pytest.raises(ValueError) as exc_info:
        session.set_model("invalid-model")
    assert "Unknown model" in str(exc_info.value)


def test_set_personality_preset():
    """Test setting personality with preset values."""
    mock_config = configparser.ConfigParser()
    mock_config["DEFAULT"] = {"api_key": "test-key"}
    session = Session(mock_config)

    # Test concise preset
    value, message = session.set_personality("concise")
    assert value == "concise"
    assert session.personality == "concise"
    assert "brief" in session.system_instruction.lower()
    assert "concise" in message

    # Test detailed preset
    value, message = session.set_personality("detailed")
    assert value == "detailed"
    assert session.personality == "detailed"
    assert "comprehensive" in session.system_instruction.lower()


def test_set_personality_invalid():
    """Test invalid personality values."""
    mock_config = configparser.ConfigParser()
    mock_config["DEFAULT"] = {"api_key": "test-key"}
    session = Session(mock_config)

    # Test invalid personality
    with pytest.raises(ValueError) as exc_info:
        session.set_personality("invalid")
    assert "Unknown personality" in str(exc_info.value)


def test_cmd_set_temperature(capsys):
    """Test /set command for temperature in REPL."""
    mock_config = configparser.ConfigParser()
    mock_config["DEFAULT"] = {"api_key": "test-key"}
    session = Session(mock_config)
    repl = Repl(session)

    # Test /set temp
    repl.handle_input("/set temp 0.8")
    captured = capsys.readouterr()
    assert "0.8" in captured.out
    assert session.temperature == 0.8


def test_cmd_set_model(capsys):
    """Test /set command for model in REPL."""
    mock_config = configparser.ConfigParser()
    mock_config["DEFAULT"] = {"api_key": "test-key"}
    session = Session(mock_config)
    repl = Repl(session)

    # Test /set model
    repl.handle_input("/set model mini")
    captured = capsys.readouterr()
    assert "claude-3-5-haiku-20241022" in captured.out
    assert session.model == "claude-3-5-haiku-20241022"


def test_cmd_set_personality(capsys):
    """Test /set command for personality in REPL."""
    mock_config = configparser.ConfigParser()
    mock_config["DEFAULT"] = {"api_key": "test-key"}
    session = Session(mock_config)
    repl = Repl(session)

    # Test /set personality
    repl.handle_input("/set personality creative")
    captured = capsys.readouterr()
    assert "creative" in captured.out
    assert session.personality == "creative"


def test_cmd_set_invalid_option(capsys):
    """Test /set command with invalid option."""
    mock_config = configparser.ConfigParser()
    mock_config["DEFAULT"] = {"api_key": "test-key"}
    session = Session(mock_config)
    repl = Repl(session)

    # Test invalid option
    repl.handle_input("/set invalid value")
    captured = capsys.readouterr()
    assert "Unknown option" in captured.out


def test_cmd_set_missing_args(capsys):
    """Test /set command with missing arguments."""
    mock_config = configparser.ConfigParser()
    mock_config["DEFAULT"] = {"api_key": "test-key"}
    session = Session(mock_config)
    repl = Repl(session)

    # Test missing value
    repl.handle_input("/set temp")
    captured = capsys.readouterr()
    assert "Usage" in captured.out


def test_temperature_presets():
    """Test all temperature presets are defined correctly."""
    assert Session.TEMPERATURE_PRESETS["rigid"] == 0.3
    assert Session.TEMPERATURE_PRESETS["default"] == 0.7
    assert Session.TEMPERATURE_PRESETS["creative"] == 1.5


def test_model_presets():
    """Test all model presets are defined correctly."""
    # Test default preset (now Claude Sonnet)
    assert Session.MODEL_PRESETS["default"] == "claude-3-5-sonnet-20241022"

    # Test mini/fast presets
    assert Session.MODEL_PRESETS["mini"] == "claude-3-5-haiku-20241022"
    assert Session.MODEL_PRESETS["fast"] == "claude-3-5-haiku-20241022"

    # Test Claude mini alternative name
    assert Session.MODEL_PRESETS["claude-mini"] == "claude-3-5-haiku-20241022"

    # Test reasoning/research presets
    assert Session.MODEL_PRESETS["reasoning"] == "o1-pro"
    assert Session.MODEL_PRESETS["research"] == "o1-pro"


def test_personality_presets():
    """Test all personality presets are defined correctly."""
    assert "default" in Session.PERSONALITY_PRESETS
    assert "concise" in Session.PERSONALITY_PRESETS
    assert "detailed" in Session.PERSONALITY_PRESETS
    assert "creative" in Session.PERSONALITY_PRESETS
    # Verify each has a system instruction
    for personality, instruction in Session.PERSONALITY_PRESETS.items():
        assert isinstance(instruction, str)
        assert len(instruction) > 0


def test_valid_models_constant():
    """Test VALID_MODELS constant is defined correctly."""
    assert len(Session.VALID_MODELS) > 0

    # Test OpenAI models
    assert "gpt-4o" in Session.VALID_MODELS
    assert "gpt-4o-mini" in Session.VALID_MODELS

    # Test reasoning models
    assert "o1-preview" in Session.VALID_MODELS
    assert "o1-mini" in Session.VALID_MODELS
    assert "o1-pro" in Session.VALID_MODELS

    # Test Claude models
    assert "claude-3-5-sonnet-20241022" in Session.VALID_MODELS
    assert "claude-3-5-haiku-20241022" in Session.VALID_MODELS

    # All models should be strings
    for model in Session.VALID_MODELS:
        assert isinstance(model, str)
        assert len(model) > 0
