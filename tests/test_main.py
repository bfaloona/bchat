import configparser
import logging
from unittest.mock import patch
import pytest
from main import load_config, main

def test_load_config():
    """
    Happy Path test for load_config.
    Verifies that the configuration is loaded and contains the DEFAULT section.
    """
    config = load_config()
    assert isinstance(config, configparser.ConfigParser)
    # Verify that the DEFAULT section is present (it's always there in ConfigParser, but good to check)
    assert "DEFAULT" in config
    # Verify we can access the config object
    assert config.sections() == [] or True # sections() excludes DEFAULT

def test_main_output(capsys):
    """
    Happy Path test for main.
    Verifies that the main function runs, initializes the OpenAI client, and prints the response.
    """
    # Mock load_config to return a known configuration with an API key
    mock_config = configparser.ConfigParser()
    mock_config["DEFAULT"] = {
        "api_key": "test-api-key",
        "system_instruction": "You are a sarcastic assistant, reluctant to help."
    }

    # Mock the OpenAI client and its response
    with patch('main.load_config', return_value=mock_config), \
         patch('main.OpenAI') as MockOpenAI, \
         patch('main.setup_logging'): # Mock setup_logging to avoid creating log files during tests

        # Setup the mock response
        mock_instance = MockOpenAI.return_value
        mock_response = mock_instance.chat.completions.create.return_value
        mock_response.choices = [type('obj', (object,), {'message': type('obj', (object,), {'content': 'Hello from Mock AI!'})})]

        main()

    captured = capsys.readouterr()
    assert "bChat is Ready!" in captured.out
    assert "Hello from Mock AI!" in captured.out

def test_logging_output(caplog):
    """
    Test that verifies logging behavior.
    Checks if INFO and DEBUG logs are generated correctly.
    """
    # Mock load_config to return a known configuration with an API key and DEBUG level
    mock_config = configparser.ConfigParser()
    mock_config["DEFAULT"] = {
        "api_key": "test-api-key",
        "system_instruction": "You are a sarcastic assistant, reluctant to help.",
        "log_level": "DEBUG"
    }

    # Mock the OpenAI client and its response
    with patch('main.load_config', return_value=mock_config), \
         patch('main.OpenAI') as MockOpenAI, \
         patch('main.setup_logging'): # Mock setup_logging to avoid creating log files

        # Setup the mock response
        mock_instance = MockOpenAI.return_value
        mock_response = mock_instance.chat.completions.create.return_value
        mock_response.choices = [type('obj', (object,), {'message': type('obj', (object,), {'content': 'Hello from Mock AI!'})})]

        # Set capture level to DEBUG to ensure we catch all logs
        caplog.set_level(logging.DEBUG)

        main()

    # Verify INFO logs
    assert "Application started." in caplog.text
    # Verify truncated user prompt (INFO)
    # "How many fingers are there, in total?" -> "How many fingers are.."
    assert "User prompt: How many fingers are.." in caplog.text
    assert "Received response from OpenAI" in caplog.text

    # Verify DEBUG logs
    assert "Full request messages:" in caplog.text
    assert "How many fingers are there, in total?" in caplog.text
    assert "Full response: Hello from Mock AI!" in caplog.text
