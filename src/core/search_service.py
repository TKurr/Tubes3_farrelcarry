# src/core/search_service.py

# This file contains the SearchService class, which orchestrates the core
# business logic of the application.

import time
import os
from typing import List, Dict, Tuple, Any

# Import our custom modules
# We now also import find_pdf_files to power our dynamic mock function
from src.core.pdf_processor import (
    find_pdf_files,
    extract_text_from_pdf,
    format_flat_text,
)
from src.core.fuzzy_matching import find_similar_word
from src.core.pattern_matching import PatternMatcherFactory

# Placeholder imports for dependencies that will be built later.
# from .database_manager import DatabaseManager


def _get_cvs_from_database() -> List[Dict[str, Any]]:
    """
    MOCK FUNCTION: Simulates fetching application details from a database
    by dynamically scanning the data directory for all available PDF files.
    This makes testing with real data easy without a live database.

    Returns:
        A list of dictionaries, where each dictionary represents an application
        with a generated detail_id and the real path to the CV.
    """
    print("[SearchService] MOCK: Dynamically scanning for CVs in data/ directory...")
    mock_db_data = []

    # Use the helper from pdf_processor to find all CVs
    for i, pdf_path in enumerate(find_pdf_files()):
        # Create a mock detail_id (e.g., starting from 101)
        detail_id = 101 + i
        mock_db_data.append({"detail_id": detail_id, "cv_path": pdf_path})

    if not mock_db_data:
        print("[SearchService] WARNING: No PDFs found in the data/ directory.")
    else:
        print(f"[SearchService] MOCK: Found {len(mock_db_data)} CVs to process.")

    return mock_db_data


class SearchService:
    """
    Orchestrates the search process, fetching application data from a (mock)
    database and using the Strategy Pattern for pattern matching.
    """

    def __init__(self):
        print("[SearchService] Initialized.")
        # self.db_manager = DatabaseManager() # This will be added in the future

    def perform_search(
        self, keywords_str: str, algorithm_type: str, num_top_matches: int
    ) -> Tuple[List[Dict[str, Any]], float, float, int, int]:
        """
        Performs an on-demand CV search using database-provided paths.
        """
        exact_start_time = time.time()
        print(
            f"[SearchService] Performing search for '{keywords_str}' using {algorithm_type}..."
        )

        keywords = [k.strip().lower() for k in keywords_str.split(",") if k.strip()]
        if not keywords:
            return [], 0.0, 0.0, 0, 0

        try:
            matcher = PatternMatcherFactory.get_matcher(algorithm_type)
        except ValueError as e:
            print(f"[SearchService] Error: {e}")
            return [], 0.0, 0.0, 0, 0

        # --- REFACTORED: Fetch from dynamic "DB" instead of filesystem ---
        all_applications = _get_cvs_from_database()

        # --- 1. EXACT MATCHING PHASE ---
        exact_matches = {}
        total_cvs_scanned_exact = 0

        for app_data in all_applications:
            detail_id = app_data["detail_id"]
            pdf_path = app_data["cv_path"]
            total_cvs_scanned_exact += 1

            # --- ADDED LOGGING ---
            print(
                f"[SearchService] Processing CV #{total_cvs_scanned_exact}: {os.path.basename(pdf_path)}"
            )

            raw_text = extract_text_from_pdf(pdf_path)
            cv_text = format_flat_text(raw_text)

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
                    "cv_path": pdf_path,
                    "total_matches": total_matches_for_cv,
                    "matched_keywords": keyword_counts,
                    "match_type": "exact",
                }

        exact_end_time = time.time()
        exact_execution_time = exact_end_time - exact_start_time

        # --- 2. FUZZY MATCHING PHASE ---
        fuzzy_start_time = time.time()
        fuzzy_matches = {}
        total_cvs_scanned_fuzzy = 0

        if len(exact_matches) < num_top_matches:
            print("[SearchService] Not enough exact matches. Starting fuzzy search.")

            unmatched_apps = [
                app for app in all_applications if app["detail_id"] not in exact_matches
            ]
            total_cvs_scanned_fuzzy = len(unmatched_apps)

            for i, app_data in enumerate(unmatched_apps):
                detail_id = app_data["detail_id"]
                pdf_path = app_data["cv_path"]

                # --- ADDED LOGGING ---
                print(
                    f"[SearchService] Fuzzy processing CV #{i+1}: {os.path.basename(pdf_path)}"
                )

                raw_text = extract_text_from_pdf(pdf_path)
                flat_text = format_flat_text(raw_text)

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
                        "cv_path": pdf_path,
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
            # MOCK: Fetch applicant details from DB using cv['detail_id']
            applicant_name = (
                os.path.basename(cv["cv_path"])
                .replace(".pdf", "")
                .replace("_", " ")
                .title()
            )

            final_results.append(
                {
                    "applicant_id": cv[
                        "detail_id"
                    ],  # In reality, this would be from applicant_info
                    "detail_id": cv["detail_id"],
                    "applicant_name": applicant_name,  # In reality, this would be from applicant_info
                    "application_role": "Role Placeholder",  # In reality, this would be from applicant_info
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
            total_cvs_scanned_exact,
            total_cvs_scanned_fuzzy,
        )

    def get_cv_summary(self, detail_id: int) -> Dict[str, Any]:
        """Retrieves and constructs a detailed summary for a given CV."""
        print(f"[SearchService] Fetching summary for detail_id: {detail_id}")
        # MOCK: In a real app, this would use the DatabaseManager and RegexExtractor
        # For now, we return a generic response since we don't know the file path from the ID alone.
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
