from abc import ABC, abstractmethod


class PatternMatcher(ABC):
    """
    Abstract base class for a pattern matching algorithm.
    All concrete algorithm implementations should inherit from this class.
    """

    @abstractmethod
    def count_occurrences(self, text: str, pattern: str) -> int:
        """
        Counts the number of non-overlapping occurrences of a pattern in a text.

        Args:
            text: The text to search within.
            pattern: The pattern to search for.

        Returns:
            The number of times the pattern occurs in the text.
        """
        pass
