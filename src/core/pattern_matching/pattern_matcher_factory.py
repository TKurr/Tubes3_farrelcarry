from .pattern_matcher_interface import PatternMatcher
from .kmp_algorithm import KMPAlgorithm
from .boyer_moore_algorithm import BoyerMooreAlgorithm
from .aho_corasick_algorithm import AhoCorasickAlgorithm


class PatternMatcherFactory:
    @staticmethod
    def get_matcher(algorithm_type: str) -> PatternMatcher:
        if algorithm_type.upper() == "KMP":
            return KMPAlgorithm()
        elif algorithm_type.upper() == "BM":
            return BoyerMooreAlgorithm()
        elif algorithm_type.upper() == "AC":
            return AhoCorasickAlgorithm()
        else:
            raise ValueError(f"Unknown pattern matching algorithm: {algorithm_type}")
