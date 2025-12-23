import os
import time
import tempfile
import pytest
from file_watcher import FileWatcher


def test_check_once_detects_changes():
    """Test check_once detects file modifications."""
    with tempfile.TemporaryDirectory() as temp_dir:
        test_file = os.path.join(temp_dir, "test.txt")
        with open(test_file, 'w') as f:
            f.write("Original")

        watcher = FileWatcher()
        watcher.mtimes[test_file] = os.path.getmtime(test_file)

        # Modify file
        time.sleep(0.1)
        with open(test_file, 'w') as f:
            f.write("Modified")

        changed = watcher.check_once()
        assert len(changed) == 1
        assert test_file in changed


def test_check_once_no_changes():
    """Test check_once with no changes returns empty list."""
    with tempfile.TemporaryDirectory() as temp_dir:
        test_file = os.path.join(temp_dir, "test.txt")
        with open(test_file, 'w') as f:
            f.write("Content")

        watcher = FileWatcher()
        watcher.mtimes[test_file] = os.path.getmtime(test_file)

        changed = watcher.check_once()
        assert len(changed) == 0


def test_check_once_deleted_file():
    """Test check_once detects deleted files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        test_file = os.path.join(temp_dir, "test.txt")
        with open(test_file, 'w') as f:
            f.write("Content")

        watcher = FileWatcher()
        watcher.mtimes[test_file] = os.path.getmtime(test_file)

        # Delete file
        os.remove(test_file)

        changed = watcher.check_once()
        assert len(changed) == 1
        assert test_file in changed


def test_watch_background_thread():
    """Test watch starts background monitoring."""
    with tempfile.TemporaryDirectory() as temp_dir:
        test_file = os.path.join(temp_dir, "test.txt")
        with open(test_file, 'w') as f:
            f.write("Original")

        callback_called = []

        def callback():
            callback_called.append(True)

        watcher = FileWatcher()
        watcher.watch([test_file], callback, interval=1)

        assert watcher.watching is True
        assert watcher.watch_thread is not None

        # Modify file
        time.sleep(0.1)
        with open(test_file, 'w') as f:
            f.write("Modified")

        # Wait for watch loop to detect change
        time.sleep(1.5)

        watcher.stop()

        # Callback should have been called
        assert len(callback_called) > 0


def test_stop_watcher():
    """Test stopping the file watcher."""
    with tempfile.TemporaryDirectory() as temp_dir:
        test_file = os.path.join(temp_dir, "test.txt")
        with open(test_file, 'w') as f:
            f.write("Content")

        watcher = FileWatcher()
        watcher.watch([test_file], lambda: None, interval=1)

        assert watcher.watching is True

        watcher.stop()

        assert watcher.watching is False
