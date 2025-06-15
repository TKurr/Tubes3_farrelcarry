from .pattern_matcher_interface import PatternMatcher


class BoyerMooreAlgorithm(PatternMatcher):
    def _preprocess_bad_character(self, pattern: str) -> dict[str, int]:
        bad_char_table = {}
        for i, char in enumerate(pattern):
            bad_char_table[char] = i
        return bad_char_table

    def count_occurrences(self, text: str, pattern: str) -> int:
        n = len(text)
        m = len(pattern)
        if m == 0 or n == 0 or m > n:
            return 0

        bad_char_table = self._preprocess_bad_character(pattern)
        shift = 0
        count = 0

        while shift <= n - m:
            j = m - 1

            while j >= 0 and pattern[j] == text[shift + j]:
                j -= 1

            if j < 0:
                count += 1
                shift += (
                    (m - bad_char_table.get(text[shift + m], -1))
                    if shift + m < n
                    else 1
                )
            else:
                bad_char_in_text = text[shift + j]
                last_occurrence_in_pattern = bad_char_table.get(bad_char_in_text, -1)

                shift += max(1, j - last_occurrence_in_pattern)

        return count
