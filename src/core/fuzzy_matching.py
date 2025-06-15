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

    dp = [[0] * (n + 1) for _ in range(m + 1)]

    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            cost = 0 if s1[i - 1] == s2[j - 1] else 1
            dp[i][j] = min(
                dp[i - 1][j] + 1,  
                dp[i][j - 1] + 1,  
                dp[i - 1][j - 1] + cost,
            ) 

    return dp[m][n]


def find_similar_word(
    keyword: str, text: str, threshold: float = 0.8
) -> tuple[str, float] | None:
    best_match = None
    highest_similarity = 0.0


    words_in_text = set(text.lower().split())

    for word in words_in_text:
        distance = calculate_levenshtein_distance(keyword, word)
        len_max = max(len(keyword), len(word))
        if len_max == 0:
            continue  

        similarity = 1.0 - (distance / len_max)

        if similarity > highest_similarity:
            highest_similarity = similarity
            best_match = word

    if highest_similarity >= threshold:
        return best_match, highest_similarity

    return None
