from .pattern_matcher_interface import PatternMatcher


class KMPAlgorithm(PatternMatcher):
    def _compute_lps_array(self, pattern: str) -> list[int]:
        m = len(pattern)
        lps = [0] * m
        length = 0
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
        n = len(text)
        m = len(pattern)
        if m == 0 or n == 0 or m > n:
            return 0

        lps = self._compute_lps_array(pattern)
        i = 0 
        j = 0 
        count = 0

        while i < n:
            if pattern[j] == text[i]:
                i += 1
                j += 1

            if j == m:
                count += 1
                j = lps[j - 1]

            elif i < n and pattern[j] != text[i]:
                if j != 0:
                    j = lps[j - 1]
                else:
                    i += 1
        return count
