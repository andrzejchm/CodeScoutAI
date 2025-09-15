from abc import ABC, abstractmethod

from core.models.code_diff import CodeDiff


class DiffProvider(ABC):
    """
    Abstract Base Class for diff providers.
    Defines the interface for any class that provides code differences.
    """

    @abstractmethod
    def get_diff(self) -> list[CodeDiff]:
        """
        Retrieves a list of code differences.
        Implementations should define how they obtain these differences
        (e.g., from a Git repository, a file system, an API).
        """
        pass

    @abstractmethod
    def get_file_contents_after_change(self, file_path: str) -> str | None:
        """
        Retrieves the contents of the file after the change.
        """
        pass

    @abstractmethod
    def get_file_contents_before_change(self, file_path: str) -> str | None:
        """
        Retrieves the contents of the file before the change.
        """
        pass
