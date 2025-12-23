import os
import tempfile
import configparser
import pytest
from repl import Repl
from session import Session


def test_cmd_add_single_file(capsys):
    """Test /add command with a single file."""
    with tempfile.TemporaryDirectory() as temp_dir:
        test_file = os.path.join(temp_dir, "test.txt")
        with open(test_file, 'w') as f:
            f.write("Test content\nLine 2")

        mock_config = configparser.ConfigParser()
        mock_config["DEFAULT"] = {"api_key": "test-key"}
        session = Session(mock_config)
        repl = Repl(session)

        repl.handle_input(f"/add {test_file}")
        captured = capsys.readouterr()

        assert "✔ Added:" in captured.out
        assert test_file in captured.out
        assert "2 lines" in captured.out


def test_cmd_add_glob_pattern(capsys):
    """Test /add command with glob pattern."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create multiple test files
        for i in range(3):
            test_file = os.path.join(temp_dir, f"test{i}.txt")
            with open(test_file, 'w') as f:
                f.write(f"Content {i}")

        mock_config = configparser.ConfigParser()
        mock_config["DEFAULT"] = {"api_key": "test-key"}
        session = Session(mock_config)
        repl = Repl(session)

        pattern = os.path.join(temp_dir, "*.txt")
        repl.handle_input(f"/add {pattern}")
        captured = capsys.readouterr()

        assert "✔ Added:" in captured.out
        assert "3 files" in captured.out


def test_cmd_add_nonexistent_file(capsys):
    """Test /add command with non-existent file."""
    mock_config = configparser.ConfigParser()
    mock_config["DEFAULT"] = {"api_key": "test-key"}
    session = Session(mock_config)
    repl = Repl(session)

    repl.handle_input("/add /nonexistent/file.txt")
    captured = capsys.readouterr()

    assert "✖ Error:" in captured.out


def test_cmd_remove_file(capsys):
    """Test /remove command."""
    with tempfile.TemporaryDirectory() as temp_dir:
        test_file = os.path.join(temp_dir, "test.txt")
        with open(test_file, 'w') as f:
            f.write("Content")

        mock_config = configparser.ConfigParser()
        mock_config["DEFAULT"] = {"api_key": "test-key"}
        session = Session(mock_config)
        repl = Repl(session)

        # Add file first
        repl.handle_input(f"/add {test_file}")
        capsys.readouterr()  # Clear output

        # Remove file
        repl.handle_input(f"/remove {test_file}")
        captured = capsys.readouterr()

        assert "✔ Removed:" in captured.out
        assert test_file in captured.out


def test_cmd_remove_not_in_context(capsys):
    """Test /remove command with file not in context."""
    mock_config = configparser.ConfigParser()
    mock_config["DEFAULT"] = {"api_key": "test-key"}
    session = Session(mock_config)
    repl = Repl(session)

    repl.handle_input("/remove /some/file.txt")
    captured = capsys.readouterr()

    assert "⚠ Warning:" in captured.out or "not in context" in captured.out


def test_cmd_context_empty(capsys):
    """Test /context command with no files loaded."""
    mock_config = configparser.ConfigParser()
    mock_config["DEFAULT"] = {"api_key": "test-key"}
    session = Session(mock_config)
    repl = Repl(session)

    repl.handle_input("/context")
    captured = capsys.readouterr()

    assert "No files loaded" in captured.out


def test_cmd_context_with_files(capsys):
    """Test /context command with loaded files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        test_file = os.path.join(temp_dir, "test.txt")
        with open(test_file, 'w') as f:
            f.write("Line 1\nLine 2\nLine 3")

        mock_config = configparser.ConfigParser()
        mock_config["DEFAULT"] = {"api_key": "test-key"}
        session = Session(mock_config)
        repl = Repl(session)

        # Add file
        repl.handle_input(f"/add {test_file}")
        capsys.readouterr()  # Clear output

        # List context
        repl.handle_input("/context")
        captured = capsys.readouterr()

        assert "Loaded Files" in captured.out
        assert test_file in captured.out
        assert "3 lines" in captured.out
        assert "Total: 1 files" in captured.out


def test_cmd_refresh(capsys):
    """Test /refresh command."""
    with tempfile.TemporaryDirectory() as temp_dir:
        test_file = os.path.join(temp_dir, "test.txt")
        with open(test_file, 'w') as f:
            f.write("Original")

        mock_config = configparser.ConfigParser()
        mock_config["DEFAULT"] = {"api_key": "test-key"}
        session = Session(mock_config)
        repl = Repl(session)

        # Add file
        repl.handle_input(f"/add {test_file}")
        capsys.readouterr()  # Clear output

        # Modify file
        import time
        time.sleep(0.1)
        with open(test_file, 'w') as f:
            f.write("Modified")

        # Refresh
        repl.handle_input("/refresh")
        captured = capsys.readouterr()

        assert "✔ Updated:" in captured.out
        assert test_file in captured.out


def test_cmd_refresh_no_changes(capsys):
    """Test /refresh command with no changes."""
    with tempfile.TemporaryDirectory() as temp_dir:
        test_file = os.path.join(temp_dir, "test.txt")
        with open(test_file, 'w') as f:
            f.write("Content")

        mock_config = configparser.ConfigParser()
        mock_config["DEFAULT"] = {"api_key": "test-key"}
        session = Session(mock_config)
        repl = Repl(session)

        # Add file
        repl.handle_input(f"/add {test_file}")
        capsys.readouterr()  # Clear output

        # Refresh without changes
        repl.handle_input("/refresh")
        captured = capsys.readouterr()

        assert "No files updated" in captured.out


def test_help_includes_new_commands(capsys):
    """Test /help command includes new context commands."""
    mock_config = configparser.ConfigParser()
    mock_config["DEFAULT"] = {"api_key": "test-key"}
    session = Session(mock_config)
    repl = Repl(session)

    repl.handle_input("/help")
    captured = capsys.readouterr()

    assert "/add" in captured.out
    assert "/remove" in captured.out
    assert "/context" in captured.out
    assert "/refresh" in captured.out
