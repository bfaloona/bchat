"""
File watching functionality for bchat.

This module provides file change detection to trigger automatic
context refresh when monitored files are modified.
"""

import os
import time
import threading
from typing import List, Callable, Dict


class FileWatcher:
    """Monitors files for changes and triggers callbacks."""

    def __init__(self):
        """Initialize the FileWatcher."""
        self.mtimes: Dict[str, float] = {}
        self.watching = False
        self.watch_thread = None
        self.callback = None
        self.interval = 5

    def watch(self, paths: List[str], callback: Callable[[], None], interval: int = 5):
        """
        Start watching files for changes in a background thread.

        Args:
            paths: List of file paths to watch.
            callback: Function to call when changes are detected.
            interval: Seconds between checks (default: 5).
        """
        self.callback = callback
        self.interval = interval

        # Initialize mtimes
        for path in paths:
            if os.path.exists(path):
                self.mtimes[path] = os.path.getmtime(path)

        # Start background thread
        self.watching = True
        self.watch_thread = threading.Thread(target=self._watch_loop, daemon=True)
        self.watch_thread.start()

    def _watch_loop(self):
        """Background loop that checks for file changes."""
        while self.watching:
            changed = self.check_once()
            if changed and self.callback:
                self.callback()
            time.sleep(self.interval)

    def check_once(self) -> List[str]:
        """
        Manually check for file changes once.

        Returns:
            List of paths that have changed.
        """
        changed_paths = []

        for path, old_mtime in list(self.mtimes.items()):
            try:
                if not os.path.exists(path):
                    # File was deleted
                    changed_paths.append(path)
                    del self.mtimes[path]
                else:
                    current_mtime = os.path.getmtime(path)
                    if current_mtime > old_mtime:
                        changed_paths.append(path)
                        self.mtimes[path] = current_mtime
            except OSError:
                # Error accessing file, consider it changed
                changed_paths.append(path)
                if path in self.mtimes:
                    del self.mtimes[path]

        return changed_paths

    def stop(self):
        """Stop watching files."""
        self.watching = False
        if self.watch_thread:
            self.watch_thread.join(timeout=1)
            self.watch_thread = None
