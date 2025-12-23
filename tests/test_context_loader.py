import tempfile
import os
from pathlib import Path
from context_loader import ContextLoader, FileContext


def test_add_file():
    """
    Test adding a single file to the context.
    """
    loader = ContextLoader()

    # Create a temporary file
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("Test content")
        temp_path = f.name

    try:
        fc = loader.add_file(temp_path)
        assert fc is not None
        assert fc.content == "Test content"
        assert fc.path == str(Path(temp_path).resolve())
        assert loader.get_total_files() == 1
    finally:
        os.unlink(temp_path)


def test_add_nonexistent_file():
    """
    Test adding a file that doesn't exist.
    """
    loader = ContextLoader()
    fc = loader.add_file("/nonexistent/file.txt")
    assert fc is None
    assert loader.get_total_files() == 0


def test_add_glob():
    """
    Test adding multiple files with glob pattern.
    """
    loader = ContextLoader()

    # Create temporary directory with files
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test files
        test_file1 = os.path.join(temp_dir, "test1.py")
        test_file2 = os.path.join(temp_dir, "test2.py")
        test_file3 = os.path.join(temp_dir, "test.txt")

        with open(test_file1, 'w') as f:
            f.write("print('test1')")
        with open(test_file2, 'w') as f:
            f.write("print('test2')")
        with open(test_file3, 'w') as f:
            f.write("text file")

        # Add Python files
        pattern = os.path.join(temp_dir, "*.py")
        added = loader.add_glob(pattern)

        assert len(added) == 2
        assert loader.get_total_files() == 2


def test_remove_file():
    """
    Test removing a file from the context.
    """
    loader = ContextLoader()

    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("Test content")
        temp_path = f.name

    try:
        loader.add_file(temp_path)
        assert loader.get_total_files() == 1

        # Remove the file
        result = loader.remove_file(temp_path)
        assert result is True
        assert loader.get_total_files() == 0

        # Try removing again
        result = loader.remove_file(temp_path)
        assert result is False
    finally:
        os.unlink(temp_path)


def test_get_context_string():
    """
    Test formatting files for context injection.
    """
    loader = ContextLoader()

    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("Test content")
        temp_path = f.name

    try:
        loader.add_file(temp_path)
        context = loader.get_context_string()

        assert f"### File: {Path(temp_path).resolve()}" in context
        assert "```" in context
        assert "Test content" in context
    finally:
        os.unlink(temp_path)


def test_max_size_limit():
    """
    Test that max_size limit is enforced.
    """
    loader = ContextLoader(max_size=100)

    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("x" * 200)  # 200 characters, exceeds limit
        temp_path = f.name

    try:
        fc = loader.add_file(temp_path)
        assert fc is None
        assert loader.get_total_files() == 0
    finally:
        os.unlink(temp_path)


def test_refresh():
    """
    Test refreshing file contents after modification.
    """
    loader = ContextLoader()

    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("Original content")
        temp_path = f.name

    try:
        fc = loader.add_file(temp_path)
        assert fc.content == "Original content"

        # Modify the file
        import time
        time.sleep(0.1)  # Ensure timestamp changes
        with open(temp_path, 'w') as f:
            f.write("Updated content")

        # Refresh
        updated = loader.refresh()

        assert len(updated) == 1
        assert str(Path(temp_path).resolve()) in updated
        assert loader.files[str(Path(temp_path).resolve())].content == "Updated content"
    finally:
        os.unlink(temp_path)


def test_list_files():
    """
    Test listing loaded files.
    """
    loader = ContextLoader()

    with tempfile.TemporaryDirectory() as temp_dir:
        test_file1 = os.path.join(temp_dir, "test1.txt")
        test_file2 = os.path.join(temp_dir, "test2.txt")

        with open(test_file1, 'w') as f:
            f.write("content1")
        with open(test_file2, 'w') as f:
            f.write("content2")

        loader.add_file(test_file1)
        loader.add_file(test_file2)

        files = loader.list_files()
        assert len(files) == 2
        assert all(isinstance(fc, FileContext) for fc in files)


def test_get_total_size():
    """
    Test calculating total size of loaded files.
    """
    loader = ContextLoader()

    with tempfile.TemporaryDirectory() as temp_dir:
        test_file1 = os.path.join(temp_dir, "test1.txt")
        test_file2 = os.path.join(temp_dir, "test2.txt")

        content1 = "a" * 100
        content2 = "b" * 200

        with open(test_file1, 'w') as f:
            f.write(content1)
        with open(test_file2, 'w') as f:
            f.write(content2)

        loader.add_file(test_file1)
        loader.add_file(test_file2)

        assert loader.get_total_size() == 300
