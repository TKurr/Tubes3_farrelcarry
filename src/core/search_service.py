# src/core/search_service.py

# This file contains the SearchService class, which now operates on
# pre-processed, in-memory data for maximum performance.

import time
import os
from typing import List, Dict, Tuple, Any

from src.core.cv_data_store import CVDataStore
from src.core.fuzzy_matching import find_similar_word
from src.core.pattern_matching import PatternMatcherFactory

# Placeholder imports for dependencies that will be built later.
# from .database_manager import DatabaseManager


class SearchService:
    """
    Orchestrates the search process using pre-processed data from the CVDataStore.
    """

    def __init__(self, cv_data_store: CVDataStore):
        print("[SearchService] Initialized with CVDataStore.")
        self.cv_data_store = cv_data_store
        # self.db_manager = DatabaseManager() # This will be added in the future

    def perform_search(
        self, keywords_str: str, algorithm_type: str, num_top_matches: int
    ) -> Tuple[List[Dict[str, Any]], float, float, int, int]:
        """
        Performs a search on the in-memory CV data.
        """
        exact_start_time = time.time()

        keywords = [k.strip().lower() for k in keywords_str.split(",") if k.strip()]
        if not keywords:
            return [], 0.0, 0.0, 0, 0

        try:
            matcher = PatternMatcherFactory.get_matcher(algorithm_type)
        except ValueError as e:
            print(f"[SearchService] Error: {e}")
            return [], 0.0, 0.0, 0, 0

        all_processed_cvs = self.cv_data_store.get_all_cvs()

        # --- ADDED LOGGING ---
        print(
            f"[SearchService] Performing in-memory search for '{keywords_str}' across {len(all_processed_cvs)} pre-processed CVs..."
        )

        # --- 1. EXACT MATCHING PHASE ---
        exact_matches = {}

        for detail_id, cv_data in all_processed_cvs.items():
            cv_text = cv_data["text"]  # The pre-parsed text string
            keyword_counts = {}
            total_matches_for_cv = 0

            for keyword in keywords:
                count = matcher.count_occurrences(cv_text, keyword)
                if count > 0:
                    keyword_counts[keyword] = count
                    total_matches_for_cv += count

            if total_matches_for_cv > 0:
                exact_matches[detail_id] = {
                    "detail_id": detail_id,
                    "cv_path": cv_data["cv_path"],
                    "total_matches": total_matches_for_cv,
                    "matched_keywords": keyword_counts,
                    "match_type": "exact",
                }

        exact_end_time = time.time()
        exact_execution_time = exact_end_time - exact_start_time

        # --- 2. FUZZY MATCHING PHASE ---
        fuzzy_start_time = time.time()
        fuzzy_matches = {}

        if len(exact_matches) < num_top_matches:
            print("[SearchService] Not enough exact matches. Starting fuzzy search.")

            unmatched_cvs = {
                k: v for k, v in all_processed_cvs.items() if k not in exact_matches
            }

            for detail_id, cv_data in unmatched_cvs.items():
                flat_text = cv_data["text"]
                fuzzy_keyword_counts = {}
                for keyword in keywords:
                    match = find_similar_word(keyword, flat_text, threshold=0.85)
                    if match:
                        best_word, score = match
                        fuzzy_keyword_counts[f"{keyword} (~{best_word})"] = (
                            f"{int(score*100)}%"
                        )

                if fuzzy_keyword_counts:
                    fuzzy_matches[detail_id] = {
                        "detail_id": detail_id,
                        "cv_path": cv_data["cv_path"],
                        "total_matches": len(fuzzy_keyword_counts),
                        "matched_keywords": fuzzy_keyword_counts,
                        "match_type": "fuzzy",
                    }

        fuzzy_end_time = time.time()
        fuzzy_execution_time = fuzzy_end_time - fuzzy_start_time

        # --- 3. COMBINE AND RANK RESULTS ---
        combined_results = {**fuzzy_matches, **exact_matches}
        sorted_cvs = sorted(
            combined_results.values(),
            key=lambda x: (x.get("match_type", ""), x.get("total_matches", 0)),
            reverse=True,
        )
        top_cvs = sorted_cvs[:num_top_matches]

        # --- 4. BUILD FINAL RESPONSE ---
        final_results = []
        for cv in top_cvs:
            applicant_name = (
                os.path.basename(cv["cv_path"])
                .replace(".pdf", "")
                .replace("_", " ")
                .title()
            )
            final_results.append(
                {
                    "applicant_id": cv["detail_id"],
                    "detail_id": cv["detail_id"],
                    "applicant_name": applicant_name,
                    "application_role": "Role Placeholder",
                    "matched_keywords": cv["matched_keywords"],
                    "total_matches": cv["total_matches"],
                    "match_type": cv["match_type"],
                    "cv_path": cv["cv_path"],
                }
            )

        return (
            final_results,
            exact_execution_time,
            fuzzy_execution_time,
            len(all_processed_cvs),
            len(fuzzy_matches),
        )

    def get_cv_summary(self, detail_id: int) -> Dict[str, Any]:
        """Retrieves and constructs a detailed summary for a given CV."""
        print(f"[SearchService] Fetching summary for detail_id: {detail_id}")
        # This will be replaced by the RegexExtractor in the future
        return {
            "applicant_name": f"Applicant {detail_id}",
            "birthdate": "N/A",
            "address": "N/A",
            "phone_number": "N/A",
            "skills": ["Mock Skill"],
            "job_history": [],
            "education": [],
            "overall_summary": "Summary not implemented yet. Requires RegexExtractor and DB call.",
            "cv_path": f"data/unknown/cv_{detail_id}.pdf",
        }
