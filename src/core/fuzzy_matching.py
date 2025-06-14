# src/core/fuzzy_matching.py

# This file implements the Levenshtein distance algorithm for fuzzy string matching.


def calculate_levenshtein_distance(s1: str, s2: str) -> int:
    """
    Calculates the Levenshtein distance between two strings.
    This is the number of edits (insertions, deletions, or substitutions)
    required to change one word into the other.

    Args:
        s1: The first string.
        s2: The second string.

    Returns:
        The Levenshtein distance as an integer.
    """
    s1 = s1.lower()
    s2 = s2.lower()
    m, n = len(s1), len(s2)

    # Initialize the distance matrix (dp table)
    # dp[i][j] will be the distance between the first i chars of s1
    # and the first j chars of s2
    dp = [[0] * (n + 1) for _ in range(m + 1)]

    # Initialize the first row and column
    # The distance from an empty string to a string of length j is j
    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j

    # Fill the rest of the matrix
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            cost = 0 if s1[i - 1] == s2[j - 1] else 1

            # The distance is the minimum of:
            # 1. Deletion from s1
            # 2. Insertion into s1
            # 3. Substitution
            dp[i][j] = min(
                dp[i - 1][j] + 1,  # Deletion
                dp[i][j - 1] + 1,  # Insertion
                dp[i - 1][j - 1] + cost,
            )  # Substitution

    # The final distance is in the bottom-right cell
    return dp[m][n]


def find_similar_word(
    keyword: str, text: str, threshold: float = 0.8
) -> tuple[str, float] | None:
    """
    Finds the best fuzzy match for a keyword within a block of text.
    It splits the text into words and calculates the similarity to the keyword.

    Args:
        keyword: The word to search for.
        text: The text block to search within.
        threshold: The similarity score required to be considered a match (0.0 to 1.0).

    Returns:
        A tuple of (best_matching_word, similarity_score) or None if no match
        above the threshold is found.
    """
    best_match = None
    highest_similarity = 0.0

    # Simple word tokenization
    words_in_text = set(text.lower().split())

    for word in words_in_text:
        distance = calculate_levenshtein_distance(keyword, word)
        # Similarity is 1 - (distance / length of the longer word)
        # This normalizes the distance to a 0-1 score.
        len_max = max(len(keyword), len(word))
        if len_max == 0:
            continue  # Avoid division by zero

        similarity = 1.0 - (distance / len_max)

        if similarity > highest_similarity:
            highest_similarity = similarity
            best_match = word

    if highest_similarity >= threshold:
        return best_match, highest_similarity

    return None
