import os
import glob as glob_module
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional


@dataclass
class FileContext:
    """Represents a file loaded into the context."""
    path: str
    content: str
    last_modified: datetime
    size: int

    def __str__(self):
        lines = len(self.content.split('\n'))
        size_kb = self.size / 1024
        return f"{self.path} ({lines} lines, {size_kb:.1f} KB)"


class ContextLoader:
    """Manages file contexts for injection into AI conversations."""

    def __init__(self, max_size: int = 50000):
        """
        Initialize the context loader.

        Args:
            max_size: Maximum total character count for all file contexts
        """
        self.max_size = max_size
        self.files: dict[str, FileContext] = {}

    def add_file(self, path: str) -> Optional[FileContext]:
        """
        Add a single file to the context.

        Args:
            path: Path to the file to add

        Returns:
            FileContext object if successful, None if file doesn't exist or is too large
        """
        path_obj = Path(path).resolve()

        if not path_obj.exists():
            return None

        if not path_obj.is_file():
            return None

        try:
            with open(path_obj, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception:
            return None

        stat = path_obj.stat()
        file_context = FileContext(
            path=str(path_obj),
            content=content,
            last_modified=datetime.fromtimestamp(stat.st_mtime),
            size=stat.st_size
        )

        # Check if adding this file would exceed max_size
        current_size = self.get_total_size()
        if current_size + len(content) > self.max_size:
            return None

        self.files[str(path_obj)] = file_context
        return file_context

    def add_glob(self, pattern: str) -> List[FileContext]:
        """
        Add multiple files matching a glob pattern.

        Args:
            pattern: Glob pattern (e.g., "src/**/*.py")

        Returns:
            List of successfully added FileContext objects
        """
        added = []
        matches = glob_module.glob(pattern, recursive=True)

        for path in matches:
            file_context = self.add_file(path)
            if file_context:
                added.append(file_context)

        return added

    def remove_file(self, path: str) -> bool:
        """
        Remove a file from the context.

        Args:
            path: Path to the file to remove

        Returns:
            True if file was removed, False if not found
        """
        path_obj = Path(path).resolve()
        path_str = str(path_obj)

        if path_str in self.files:
            del self.files[path_str]
            return True
        return False

    def get_context_string(self) -> str:
        """
        Format all loaded files for injection into the system prompt.

        Returns:
            Formatted string containing all file contents
        """
        if not self.files:
            return ""

        parts = []
        for file_context in self.files.values():
            # Detect file extension for syntax highlighting
            ext = Path(file_context.path).suffix.lstrip('.')
            # Map common extensions to markdown language identifiers
            lang_map = {
                'py': 'python', 'js': 'javascript', 'ts': 'typescript',
                'java': 'java', 'c': 'c', 'cpp': 'cpp', 'cc': 'cpp',
                'h': 'c', 'hpp': 'cpp', 'cs': 'csharp', 'go': 'go',
                'rs': 'rust', 'rb': 'ruby', 'php': 'php', 'swift': 'swift',
                'kt': 'kotlin', 'scala': 'scala', 'sh': 'bash', 'bash': 'bash',
                'yaml': 'yaml', 'yml': 'yaml', 'json': 'json', 'xml': 'xml',
                'html': 'html', 'css': 'css', 'sql': 'sql', 'md': 'markdown'
            }
            lang = lang_map.get(ext, '')

            parts.append(f"### File: {file_context.path}")
            parts.append(f"```{lang}")
            parts.append(file_context.content)
            parts.append("```")
            parts.append("")

        return "\n".join(parts)

    def list_files(self) -> List[FileContext]:
        """
        Get list of all loaded files.

        Returns:
            List of FileContext objects
        """
        return list(self.files.values())

    def refresh(self) -> List[str]:
        """
        Re-read all loaded files and detect changes.

        Returns:
            List of paths that were updated
        """
        updated = []

        for path in list(self.files.keys()):
            path_obj = Path(path)

            if not path_obj.exists():
                del self.files[path]
                continue

            try:
                stat = path_obj.stat()
                current_mtime = datetime.fromtimestamp(stat.st_mtime)

                if current_mtime > self.files[path].last_modified:
                    with open(path_obj, 'r', encoding='utf-8') as f:
                        content = f.read()

                    self.files[path] = FileContext(
                        path=path,
                        content=content,
                        last_modified=current_mtime,
                        size=stat.st_size
                    )
                    updated.append(path)
            except Exception:
                continue

        return updated

    def get_total_size(self) -> int:
        """
        Get total character count of all loaded files.

        Returns:
            Total character count
        """
        return sum(len(fc.content) for fc in self.files.values())

    def get_total_files(self) -> int:
        """
        Get count of loaded files.

        Returns:
            Number of loaded files
        """
        return len(self.files)
