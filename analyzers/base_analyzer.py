"""
base_analyzer.py — Abstract base class enforcing the Strategy pattern.

All analyzers must implement `analyze(repo_data: RepoData)` and return
their typed result model. This contract guarantees:
  - Consistent interface for ScoreEngine to call any analyzer uniformly
  - Testability: any analyzer can be substituted with a mock
  - Extensibility: new analyzers are added without touching existing code
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from models.audit_report import RepoData

logger = logging.getLogger(__name__)

# Generic type variable bound to any analyzer result model
T = TypeVar("T")


class BaseAnalyzer(ABC, Generic[T]):
    """
    Abstract base class for all project analyzers.

    Subclasses implement `analyze()` and return a typed Pydantic result model.
    The base class provides shared utility methods for file-tree inspection.
    """

    @abstractmethod
    def analyze(self, repo_data: RepoData) -> T:
        """
        Run the analysis and return a populated result model.

        Args:
            repo_data: The fully-fetched repository data.

        Returns:
            A typed Pydantic model containing score and per-check details.
        """
        ...

    # ------------------------------------------------------------------
    # Shared utility methods available to all analyzers
    # ------------------------------------------------------------------

    @staticmethod
    def file_exists(file_tree: list[str], filename: str) -> bool:
        """Return True if an exact filename exists anywhere in the tree."""
        filename_lower = filename.lower()
        return any(
            path.lower() == filename_lower or path.lower().endswith(f"/{filename_lower}")
            for path in file_tree
        )

    @staticmethod
    def folder_exists(file_tree: list[str], folder_name: str) -> bool:
        """Return True if a folder with the given name exists at any depth."""
        folder_lower = folder_name.lower()
        return any(
            part.lower() == folder_lower
            for path in file_tree
            for part in path.split("/")
        )

    @staticmethod
    def any_file_exists(file_tree: list[str], filenames: list[str]) -> str | None:
        """
        Return the first matching filename from the list, or None.
        Useful for detecting any one of several equivalent files.
        """
        for filename in filenames:
            filename_lower = filename.lower()
            for path in file_tree:
                if (
                    path.lower() == filename_lower
                    or path.lower().endswith(f"/{filename_lower}")
                ):
                    return path
        return None

    @staticmethod
    def any_folder_exists(file_tree: list[str], folder_names: list[str]) -> str | None:
        """
        Return the first matching folder name from the list, or None.
        """
        for folder_name in folder_names:
            folder_lower = folder_name.lower()
            for path in file_tree:
                for part in path.split("/"):
                    if part.lower() == folder_lower:
                        return folder_name
        return None

    @staticmethod
    def count_files_matching(file_tree: list[str], patterns: list[str]) -> int:
        """Count files whose path contains any of the given patterns."""
        count = 0
        for path in file_tree:
            path_lower = path.lower()
            if any(p.lower() in path_lower for p in patterns):
                count += 1
        return count

    @staticmethod
    def keyword_in_text(text: str, keywords: list[str]) -> bool:
        """Return True if any keyword appears in the text (case-insensitive)."""
        text_lower = text.lower()
        return any(kw.lower() in text_lower for kw in keywords)
