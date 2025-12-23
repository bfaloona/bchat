import configparser
import tempfile
import os
from unittest.mock import patch
from repl import Repl
from session import Session


def test_context_commands(capsys):
    """
    Test file context commands (/add, /context, /remove, /refresh).
    """
    mock_config = configparser.ConfigParser()
    mock_config["DEFAULT"] = {
        "api_key": "test-key",
        "context_max_size": "50000"
    }

    session = Session(mock_config)
    repl = Repl(session)

    # Create a temporary test file
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.py') as f:
        f.write("print('Hello')")
        temp_path = f.name

    try:
        # Test /add command
        repl.handle_input(f"/add {temp_path}")
        captured = capsys.readouterr()
        assert "Added:" in captured.out
        assert temp_path in captured.out or "lines" in captured.out

        # Test /context command
        repl.handle_input("/context")
        captured = capsys.readouterr()
        assert "Loaded Files" in captured.out or "file(s)" in captured.out

        # Test /refresh command
        repl.handle_input("/refresh")
        captured = capsys.readouterr()
        assert "Updated" in captured.out or "No files were updated" in captured.out

        # Test /remove command
        repl.handle_input(f"/remove {temp_path}")
        captured = capsys.readouterr()
        assert "Removed:" in captured.out

        # Verify context is empty
        repl.handle_input("/context")
        captured = capsys.readouterr()
        assert "No files loaded" in captured.out
    finally:
        os.unlink(temp_path)


def test_add_glob_pattern(capsys):
    """
    Test /add command with glob pattern.
    """
    mock_config = configparser.ConfigParser()
    mock_config["DEFAULT"] = {
        "api_key": "test-key",
        "context_max_size": "50000"
    }

    session = Session(mock_config)
    repl = Repl(session)

    # Create temporary directory with test files
    with tempfile.TemporaryDirectory() as temp_dir:
        test_file1 = os.path.join(temp_dir, "test1.py")
        test_file2 = os.path.join(temp_dir, "test2.py")

        with open(test_file1, 'w') as f:
            f.write("print('test1')")
        with open(test_file2, 'w') as f:
            f.write("print('test2')")

        # Test /add with glob pattern
        pattern = os.path.join(temp_dir, "*.py")
        repl.handle_input(f"/add {pattern}")
        captured = capsys.readouterr()
        assert "Added:" in captured.out
        # Should have added 2 files
        assert "file(s)" in captured.out or "2" in captured.out


def test_context_integration_with_messages():
    """
    Test that context loader is integrated into session messages.
    """
    mock_config = configparser.ConfigParser()
    mock_config["DEFAULT"] = {
        "api_key": "test-key",
        "system_instruction": "You are helpful.",
        "context_max_size": "50000"
    }

    session = Session(mock_config)

    # Create a temporary test file
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.py') as f:
        f.write("def test():\n    pass")
        temp_path = f.name

    try:
        # Add file to context
        session.context_loader.add_file(temp_path)

        # Get messages - should include file content in system message
        messages = session.get_messages()

        # System message should contain the original instruction
        assert "You are helpful." in messages[0]["content"]

        # System message should also contain the file context
        assert "### File:" in messages[0]["content"]
        assert "def test():" in messages[0]["content"]
    finally:
        os.unlink(temp_path)
