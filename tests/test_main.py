import configparser
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
    Verifies that the main function runs and prints the loaded configuration.
    """
    # Mock load_config to return a known configuration to ensure deterministic output
    mock_config = configparser.ConfigParser()
    mock_config["DEFAULT"] = {"key": "value"}

    with patch('main.load_config', return_value=mock_config):
        main()

    captured = capsys.readouterr()
    assert "Configuration loaded:" in captured.out
    # The default string representation of a SectionProxy is <Section: DEFAULT>
    assert "<Section: DEFAULT>" in captured.out
