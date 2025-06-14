# src/core/pattern_matching/boyer_moore_algorithm.py

# This file contains the implementation of the Boyer-Moore pattern
# matching algorithm, using the Bad Character Heuristic.

from .pattern_matcher_interface import PatternMatcher


class BoyerMooreAlgorithm(PatternMatcher):
    """
    Implements the Boyer-Moore pattern matching algorithm.
    This implementation uses the Bad Character Heuristic for efficient shifting.
    """

    def _preprocess_bad_character(self, pattern: str) -> dict[str, int]:
        """
        Creates the "bad character" table. This table stores the last
        occurrence index of each character in the pattern.
        """
        bad_char_table = {}
        for i, char in enumerate(pattern):
            bad_char_table[char] = i
        return bad_char_table

    def count_occurrences(self, text: str, pattern: str) -> int:
        """
        Counts occurrences of the pattern in the text using Boyer-Moore.
        """
        n = len(text)
        m = len(pattern)
        if m == 0 or n == 0 or m > n:
            return 0

        bad_char_table = self._preprocess_bad_character(pattern)
        shift = 0
        count = 0

        while shift <= n - m:
            j = m - 1  # Start comparison from the end of the pattern

            while j >= 0 and pattern[j] == text[shift + j]:
                j -= 1

            if j < 0:
                # A match was found
                count += 1
                # Shift the pattern to align with the next possible match.
                # If the character after the match exists in the pattern,
                # shift by its last occurrence, otherwise shift by pattern length.
                shift += (
                    (m - bad_char_table.get(text[shift + m], -1))
                    if shift + m < n
                    else 1
                )
            else:
                # A mismatch occurred at text[shift + j].
                # Shift the pattern based on the bad character rule.
                bad_char_in_text = text[shift + j]
                last_occurrence_in_pattern = bad_char_table.get(bad_char_in_text, -1)

                # The shift is the maximum of 1 (to ensure progress) or the
                # calculated shift from the bad character rule.
                shift += max(1, j - last_occurrence_in_pattern)

        return count
