# src/core/pattern_matching/kmp_algorithm.py

# This file contains the implementation of the Knuth-Morris-Pratt (KMP)
# pattern matching algorithm.

from .pattern_matcher_interface import PatternMatcher


class KMPAlgorithm(PatternMatcher):
    """
    Implements the KMP pattern matching algorithm.
    It preprocesses the pattern to create a Longest Proper Prefix Suffix (LPS)
    array, which helps avoid redundant comparisons.
    """

    def _compute_lps_array(self, pattern: str) -> list[int]:
        """
        Computes the Longest Proper Prefix Suffix (LPS) array for the pattern.
        lps[i] stores the length of the longest proper prefix of pattern[0..i]
        which is also a suffix of pattern[0..i].
        """
        m = len(pattern)
        lps = [0] * m
        length = 0  # Length of the previous longest prefix suffix
        i = 1

        while i < m:
            if pattern[i] == pattern[length]:
                length += 1
                lps[i] = length
                i += 1
            else:
                if length != 0:
                    length = lps[length - 1]
                else:
                    lps[i] = 0
                    i += 1
        return lps

    def count_occurrences(self, text: str, pattern: str) -> int:
        """
        Counts occurrences of the pattern in the text using the KMP algorithm.
        """
        n = len(text)
        m = len(pattern)
        if m == 0 or n == 0 or m > n:
            return 0

        lps = self._compute_lps_array(pattern)
        i = 0  # index for text
        j = 0  # index for pattern
        count = 0

        while i < n:
            if pattern[j] == text[i]:
                i += 1
                j += 1

            if j == m:
                count += 1
                # To find non-overlapping matches, we could reset j to 0.
                # To find all matches (including overlapping), we use the LPS array.
                # Standard KMP finds all matches, so we follow that.
                j = lps[j - 1]

            elif i < n and pattern[j] != text[i]:
                if j != 0:
                    j = lps[j - 1]
                else:
                    i += 1
        return count
