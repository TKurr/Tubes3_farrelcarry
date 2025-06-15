from .pattern_matcher_interface import PatternMatcher
from collections import deque


class TrieNode:
    def __init__(self):
        self.children = {}
        self.failure = None
        self.output = []


class AhoCorasickAlgorithm(PatternMatcher):
    def __init__(self):
        self.root = TrieNode()
        self.patterns = []

    def _build_trie(self, patterns: list[str]) -> None:
        for pattern_idx, pattern in enumerate(patterns):
            current = self.root
            for char in pattern:
                if char not in current.children:
                    current.children[char] = TrieNode()
                current = current.children[char]
            current.output.append(pattern_idx)

    def _build_failure_links(self) -> None:
        queue = deque()
        
        # Set failure links for level 1 nodes (direct children of root)
        for child in self.root.children.values():
            child.failure = self.root
            queue.append(child)

        # Build failure links for deeper levels
        while queue:
            current = queue.popleft()
            
            for char, child in current.children.items():
                queue.append(child)
                
                # Find the failure link
                failure = current.failure
                while failure is not None and char not in failure.children:
                    failure = failure.failure
                
                if failure is not None:
                    child.failure = failure.children[char]
                else:
                    child.failure = self.root
                
                # Add output from failure link
                child.output.extend(child.failure.output)

    def _search_patterns(self, text: str) -> dict[int, int]:
        pattern_counts = {i: 0 for i in range(len(self.patterns))}
        current = self.root
        
        for char in text:
            # Follow failure links until we find a match or reach root
            while current is not None and char not in current.children:
                current = current.failure
            
            if current is None:
                current = self.root
            else:
                current = current.children[char]
                
                # Record all pattern matches at this position
                for pattern_idx in current.output:
                    pattern_counts[pattern_idx] += 1
        
        return pattern_counts

    def count_occurrences(self, text: str, pattern: str) -> int:
        if not pattern or not text or len(pattern) > len(text):
            return 0
        
        # Initialize for single pattern
        self.patterns = [pattern]
        self.root = TrieNode()
        
        # Build trie and failure links
        self._build_trie(self.patterns)
        self._build_failure_links()
        
        # Search and return count for the single pattern
        pattern_counts = self._search_patterns(text)
        return pattern_counts[0]

    def count_multiple_patterns(self, text: str, patterns: list[str]) -> dict[str, int]:
        if not patterns or not text:
            return {pattern: 0 for pattern in patterns}
        
        # Filter out empty patterns
        valid_patterns = [p for p in patterns if p and len(p) <= len(text)]
        if not valid_patterns:
            return {pattern: 0 for pattern in patterns}
        
        # Initialize
        self.patterns = valid_patterns
        self.root = TrieNode()
        
        # Build trie and failure links
        self._build_trie(self.patterns)
        self._build_failure_links()
        
        # Search and return counts
        pattern_counts = self._search_patterns(text)
        
        # Map back to original pattern strings
        result = {}
        for i, pattern in enumerate(valid_patterns):
            result[pattern] = pattern_counts[i]
        
        # Add zero counts for invalid patterns
        for pattern in patterns:
            if pattern not in result:
                result[pattern] = 0
                
        return result