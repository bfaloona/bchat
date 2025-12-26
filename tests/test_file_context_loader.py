import asyncio
import os
import tempfile
import time
import pytest
import pytest_asyncio
from file_context_loader import FileContextLoader, FileContext


@pytest.mark.asyncio
async def test_add_single_file():
    """Test adding a single file to context."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a test file
        test_file = os.path.join(temp_dir, "test.txt")
        with open(test_file, 'w') as f:
            f.write("Line 1\nLine 2\nLine 3")

        loader = FileContextLoader()
        context = await loader.add_file(test_file)

        assert context.path == os.path.abspath(test_file)
        assert context.content == "Line 1\nLine 2\nLine 3"
        assert context.line_count == 3
        assert context.size == 20


@pytest.mark.asyncio
async def test_add_file_not_found():
    """Test adding a non-existent file raises FileNotFoundError."""
    loader = FileContextLoader()
    with pytest.raises(FileNotFoundError):
        await loader.add_file("/nonexistent/file.txt")


@pytest.mark.asyncio
async def test_add_binary_file():
    """Test adding a binary file raises ValueError."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a binary file with non-UTF-8 bytes
        test_file = os.path.join(temp_dir, "test.bin")
        with open(test_file, 'wb') as f:
            # Write bytes that will fail UTF-8 decoding
            f.write(b'\x80\x81\x82\x83\x84\x85')

        loader = FileContextLoader()
        with pytest.raises(ValueError, match="Binary file not supported"):
            await loader.add_file(test_file)


@pytest.mark.asyncio
async def test_add_file_too_large():
    """Test adding a file larger than max_size raises ValueError."""
    with tempfile.TemporaryDirectory() as temp_dir:
        test_file = os.path.join(temp_dir, "large.txt")
        with open(test_file, 'w') as f:
            f.write("x" * 1000)

        loader = FileContextLoader(max_size=500)
        with pytest.raises(ValueError, match="File too large"):
            await loader.add_file(test_file)


@pytest.mark.asyncio
async def test_add_glob_pattern():
    """Test adding files using glob pattern."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test files
        for i in range(3):
            test_file = os.path.join(temp_dir, f"test{i}.txt")
            with open(test_file, 'w') as f:
                f.write(f"Content {i}")

        loader = FileContextLoader()
        pattern = os.path.join(temp_dir, "*.txt")
        contexts = await loader.add_glob(pattern)

        assert len(contexts) == 3
        assert all(isinstance(ctx, FileContext) for ctx in contexts)


@pytest.mark.asyncio
async def test_add_glob_no_matches():
    """Test glob pattern with no matches raises ValueError."""
    loader = FileContextLoader()
    with pytest.raises(ValueError, match="No files match pattern"):
        await loader.add_glob("/nonexistent/*.txt")


@pytest.mark.asyncio
async def test_remove_file():
    """Test removing a file from context."""
    with tempfile.TemporaryDirectory() as temp_dir:
        test_file = os.path.join(temp_dir, "test.txt")
        with open(test_file, 'w') as f:
            f.write("Test content")

        loader = FileContextLoader()
        await loader.add_file(test_file)

        # Remove the file
        removed = loader.remove_file(test_file)
        assert removed is True

        # Try removing again
        removed = loader.remove_file(test_file)
        assert removed is False


@pytest.mark.asyncio
async def test_list_files():
    """Test listing all loaded files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test files
        files = []
        for i in range(3):
            test_file = os.path.join(temp_dir, f"test{i}.txt")
            with open(test_file, 'w') as f:
                f.write(f"Content {i}")
            files.append(test_file)

        loader = FileContextLoader()
        for f in files:
            await loader.add_file(f)

        loaded = loader.list_files()
        assert len(loaded) == 3
        assert all(isinstance(ctx, FileContext) for ctx in loaded)


@pytest.mark.asyncio
async def test_format_for_prompt():
    """Test formatting context string for AI."""
    with tempfile.TemporaryDirectory() as temp_dir:
        test_file = os.path.join(temp_dir, "test.py")
        with open(test_file, 'w') as f:
            f.write("def hello():\n    print('Hello')")

        loader = FileContextLoader()
        await loader.add_file(test_file)

        context_str = loader.format_for_prompt()
        assert "### File:" in context_str
        assert test_file in context_str
        assert "```" in context_str
        assert "def hello():" in context_str


@pytest.mark.asyncio
async def test_format_for_prompt_empty():
    """Test getting context string with no files loaded."""
    loader = FileContextLoader()
    context_str = loader.format_for_prompt()
    assert context_str == ""


@pytest.mark.asyncio
async def test_refresh_detects_changes():
    """Test refresh detects and updates modified files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        test_file = os.path.join(temp_dir, "test.txt")
        with open(test_file, 'w') as f:
            f.write("Original content")

        loader = FileContextLoader()
        await loader.add_file(test_file)

        # Modify the file
        time.sleep(0.1)  # Ensure mtime changes
        with open(test_file, 'w') as f:
            f.write("Updated content")

        # Refresh should detect the change
        updated = await loader.refresh()
        assert len(updated) == 1
        assert test_file in updated[0]

        # Check content was updated
        files = loader.list_files()
        assert files[0].content == "Updated content"


@pytest.mark.asyncio
async def test_refresh_no_changes():
    """Test refresh with no changes returns empty list."""
    with tempfile.TemporaryDirectory() as temp_dir:
        test_file = os.path.join(temp_dir, "test.txt")
        with open(test_file, 'w') as f:
            f.write("Content")

        loader = FileContextLoader()
        await loader.add_file(test_file)

        # Refresh without changes
        updated = await loader.refresh()
        assert len(updated) == 0


@pytest.mark.asyncio
async def test_get_total_size():
    """Test getting total size of loaded files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test files with known sizes
        for i in range(3):
            test_file = os.path.join(temp_dir, f"test{i}.txt")
            with open(test_file, 'w') as f:
                f.write("x" * 10)  # 10 characters each

        loader = FileContextLoader()
        pattern = os.path.join(temp_dir, "*.txt")
        await loader.add_glob(pattern)

        total_size = loader.get_total_size()
        assert total_size == 30


@pytest.mark.asyncio
async def test_get_total_lines():
    """Test getting total line count of loaded files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test files with known line counts
        test_file1 = os.path.join(temp_dir, "test1.txt")
        with open(test_file1, 'w') as f:
            f.write("Line 1\nLine 2")

        test_file2 = os.path.join(temp_dir, "test2.txt")
        with open(test_file2, 'w') as f:
            f.write("A\nB\nC")

        loader = FileContextLoader()
        await loader.add_file(test_file1)
        await loader.add_file(test_file2)

        total_lines = loader.get_total_lines()
        assert total_lines == 5


@pytest.mark.asyncio
async def test_context_respects_max_size():
    """Test that context string respects max_size limit."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create files that exceed max_size when combined
        test_file1 = os.path.join(temp_dir, "test1.txt")
        with open(test_file1, 'w') as f:
            f.write("x" * 100)

        test_file2 = os.path.join(temp_dir, "test2.txt")
        with open(test_file2, 'w') as f:
            f.write("y" * 100)

        # max_size of 150 means only first file (100 chars) fits,
        # second file would exceed it
        loader = FileContextLoader(max_size=150)
        await loader.add_file(test_file1)
        await loader.add_file(test_file2)

        context_str = loader.format_for_prompt()
        # Should include first file content
        assert "xxx" in context_str
        # Should show truncation message for second file or not include it
        assert "truncated" in context_str.lower() or "yyy" not in context_str
