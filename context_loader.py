"""
File context management for bchat.

This module provides functionality to load and manage file contents
that can be injected into the AI conversation context.
"""

import os
import glob as glob_module
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional


@dataclass
class FileContext:
    """Represents a loaded file with its metadata."""
    path: str
    content: str
    last_modified: float
    size: int
    line_count: int


class ContextLoader:
    """Manages file contexts for injection into AI conversations."""

    def __init__(self, max_size: int = 50000):
        """
        Initialize the ContextLoader.

        Args:
            max_size: Maximum total size in characters for all file contexts.
        """
        self.max_size = max_size
        self.files: dict[str, FileContext] = {}

    def add_file(self, path: str) -> FileContext:
        """
        Add a single file to the context.

        Args:
            path: Path to the file (relative or absolute).

        Returns:
            FileContext object for the added file.

        Raises:
            FileNotFoundError: If the file doesn't exist.
            PermissionError: If the file cannot be read.
            ValueError: If the file is binary or too large.
        """
        # Convert to absolute path
        abs_path = os.path.abspath(path)

        if not os.path.exists(abs_path):
            raise FileNotFoundError(f"File not found: {path}")

        if not os.path.isfile(abs_path):
            raise ValueError(f"Not a file: {path}")

        # Check file size
        file_size = os.path.getsize(abs_path)
        if file_size > self.max_size:
            raise ValueError(f"File too large: {path} ({file_size} bytes > {self.max_size} bytes)")

        # Read file content
        try:
            with open(abs_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            raise ValueError(f"Binary file not supported: {path}")
        except PermissionError as e:
            raise PermissionError(f"Cannot read file: {path}") from e

        # Get file metadata
        stat = os.stat(abs_path)
        last_modified = stat.st_mtime
        line_count = content.count('\n') + (1 if content and not content.endswith('\n') else 0)

        # Create FileContext
        file_context = FileContext(
            path=abs_path,
            content=content,
            last_modified=last_modified,
            size=len(content),
            line_count=line_count
        )

        # Store in dictionary
        self.files[abs_path] = file_context

        return file_context

    def add_glob(self, pattern: str) -> List[FileContext]:
        """
        Add files matching a glob pattern to the context.

        Args:
            pattern: Glob pattern (e.g., "*.py", "src/**/*.js").

        Returns:
            List of FileContext objects for added files.

        Raises:
            ValueError: If pattern doesn't match any files.
        """
        # Expand glob pattern
        matched_files = glob_module.glob(pattern, recursive=True)

        if not matched_files:
            raise ValueError(f"No files match pattern: {pattern}")

        # Filter to only include files (not directories)
        matched_files = [f for f in matched_files if os.path.isfile(f)]

        if not matched_files:
            raise ValueError(f"No files match pattern: {pattern}")

        added_contexts = []
        errors = []

        for file_path in matched_files:
            try:
                context = self.add_file(file_path)
                added_contexts.append(context)
            except (ValueError, PermissionError) as e:
                # Collect errors but continue processing other files
                errors.append(f"{file_path}: {str(e)}")

        if not added_contexts and errors:
            raise ValueError(f"Failed to add any files. Errors: {'; '.join(errors)}")

        return added_contexts

    def remove_file(self, path: str) -> bool:
        """
        Remove a file from the context.

        Args:
            path: Path to the file to remove.

        Returns:
            True if file was removed, False if file was not in context.
        """
        # Try both as-is and as absolute path
        abs_path = os.path.abspath(path)

        if abs_path in self.files:
            del self.files[abs_path]
            return True
        elif path in self.files:
            del self.files[path]
            return True

        return False

    def get_context_string(self) -> str:
        """
        Get formatted context string for injection into system prompt.

        Returns:
            Formatted string with all file contents.
        """
        if not self.files:
            return ""

        parts = []
        total_size = 0

        for file_context in self.files.values():
            # Check if adding this file would exceed max_size
            if total_size + file_context.size > self.max_size:
                parts.append(f"\n### File: {file_context.path}\n```\n[Content truncated - size limit exceeded]\n```")
                break

            # Format file content
            parts.append(f"\n### File: {file_context.path}\n```\n{file_context.content}\n```")
            total_size += file_context.size

        return '\n'.join(parts)

    def list_files(self) -> List[FileContext]:
        """
        Get list of all loaded files.

        Returns:
            List of FileContext objects.
        """
        return list(self.files.values())

    def refresh(self) -> List[str]:
        """
        Re-read files that have been modified since last load.

        Returns:
            List of paths that were updated.
        """
        updated_paths = []

        for path, file_context in list(self.files.items()):
            try:
                # Check if file still exists
                if not os.path.exists(path):
                    # File was deleted, remove from context
                    del self.files[path]
                    continue

                # Check if file was modified
                current_mtime = os.path.getmtime(path)
                if current_mtime > file_context.last_modified:
                    # Re-read the file
                    self.add_file(path)
                    updated_paths.append(path)

            except (ValueError, PermissionError, FileNotFoundError):
                # If we can't read the file anymore, remove it from context
                del self.files[path]

        return updated_paths

    def get_total_size(self) -> int:
        """
        Get total size of all loaded file contents.

        Returns:
            Total size in characters.
        """
        return sum(fc.size for fc in self.files.values())

    def get_total_lines(self) -> int:
        """
        Get total line count of all loaded files.

        Returns:
            Total line count.
        """
        return sum(fc.line_count for fc in self.files.values())
