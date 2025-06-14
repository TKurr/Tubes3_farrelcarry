# src/core/pattern_matching/pattern_matcher_factory.py

# This file contains the factory for creating pattern matching algorithm instances.

from .pattern_matcher_interface import PatternMatcher
from .kmp_algorithm import KMPAlgorithm
from .boyer_moore_algorithm import BoyerMooreAlgorithm


class PatternMatcherFactory:
    """
    A factory class to create instances of pattern matching algorithms.
    This encapsulates the creation logic and decouples the SearchService
    from the concrete algorithm classes.
    """

    @staticmethod
    def get_matcher(algorithm_type: str) -> PatternMatcher:
        """
        Returns an instance of the requested pattern matching algorithm.

        Args:
            algorithm_type: A string identifier for the algorithm (e.g., "KMP", "BM").

        Returns:
            An instance of a class that implements the PatternMatcher interface.

        Raises:
            ValueError: If the requested algorithm_type is unknown.
        """
        if algorithm_type.upper() == "KMP":
            return KMPAlgorithm()
        elif algorithm_type.upper() == "BM":
            return BoyerMooreAlgorithm()
        else:
            raise ValueError(f"Unknown pattern matching algorithm: {algorithm_type}")
