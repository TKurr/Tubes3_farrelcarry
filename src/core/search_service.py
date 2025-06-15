# src/core/search_service.py

import time
import os
from typing import List, Dict, Tuple, Any
import traceback  # For detailed error logging

from src.core.cv_data_store import CVDataStore
from src.core.fuzzy_matching import find_similar_word
from src.core.pattern_matching import PatternMatcherFactory

# The new, robust information extractor
from src.core.pdf_processor import extract_hybrid_info


class SearchService:
    def __init__(self, cv_data_store: CVDataStore, db_manager=None):
        print("[SearchService] Initialized with CVDataStore and DatabaseManager.")
        self.cv_data_store = cv_data_store
        self.db_manager = db_manager

    def perform_search(
        self, keywords_str: str, algorithm_type: str, num_top_matches: int
    ) -> Tuple[List[Dict[str, Any]], float, float, int, int]:
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
        print(
            f"[SearchService] Performing in-memory search for '{keywords_str}' across {len(all_processed_cvs)} pre-processed CVs..."
        )

        exact_matches = {}
        for detail_id, cv_data in all_processed_cvs.items():
            cv_text = cv_data.get("flat_text", "")
            if not cv_text:
                continue

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
        exact_execution_time = time.time() - exact_start_time

        fuzzy_matches = {}
        fuzzy_start_time = time.time()
        if len(exact_matches) < num_top_matches:
            unmatched_cvs = {
                k: v for k, v in all_processed_cvs.items() if k not in exact_matches
            }
            for detail_id, cv_data in unmatched_cvs.items():
                flat_text = cv_data.get("flat_text", "")
                if not flat_text:
                    continue

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
        fuzzy_execution_time = time.time() - fuzzy_start_time

        combined_results = {**fuzzy_matches, **exact_matches}
        sorted_cvs = sorted(
            combined_results.values(),
            key=lambda x: (x.get("match_type", ""), x.get("total_matches", 0)),
            reverse=True,
        )
        top_cvs = sorted_cvs[:num_top_matches]

        final_results = []
        for cv_match_data in top_cvs:
            applicant_name, application_role, applicant_id = self._get_applicant_info(
                cv_match_data["detail_id"]
            )
            final_results.append(
                {
                    "applicant_id": applicant_id,
                    "detail_id": cv_match_data["detail_id"],
                    "applicant_name": applicant_name,
                    "application_role": application_role,
                    "matched_keywords": cv_match_data["matched_keywords"],
                    "total_matches": cv_match_data["total_matches"],
                    "match_type": cv_match_data["match_type"],
                    "cv_path": cv_match_data["cv_path"],
                }
            )
        return (
            final_results,
            exact_execution_time,
            fuzzy_execution_time,
            len(all_processed_cvs),
            len(fuzzy_matches),
        )

    def _get_applicant_info(self, detail_id: int) -> tuple:
        """Helper method to get applicant information from the database or cache."""
        cv_entry = self.cv_data_store.get_all_cvs().get(detail_id)
        if not cv_entry:
            return "Applicant Not Found", "Role Not Found", detail_id

        db_info = cv_entry.get("db_info", {})
        cached_role = db_info.get("application_role", "Unknown Role")
        cached_applicant_id = db_info.get("applicant_id", detail_id)

        if not self.db_manager:
            return "Unknown Applicant (No DB)", cached_role, cached_applicant_id

        try:
            applicant = self.db_manager.get_applicant_by_id(cached_applicant_id)
            if applicant:
                full_name = f"{applicant.first_name} {applicant.last_name}".strip()
                return full_name, cached_role, applicant.applicant_id
            else:
                return "DB Applicant Not Found", cached_role, cached_applicant_id
        except Exception as e:
            print(
                f"[SearchService] Error in _get_applicant_info for detail_id {detail_id}: {e}"
            )
            return "DB Error", cached_role, cached_applicant_id

    def get_cv_summary(self, detail_id: int) -> Dict[str, Any]:
        print(f"[SearchService] Fetching summary for detail_id: {detail_id}")

        cv_content = self.cv_data_store.get_all_cvs().get(detail_id)
        if not cv_content or "structured_text" not in cv_content:
            return {"error": f"No structured_text found for detail_id: {detail_id}"}

        try:
            structured_cv_text = cv_content["structured_text"]
            extracted_info = (
                extract_hybrid_info(structured_cv_text) if structured_cv_text else {}
            )

            applicant_name, application_role, _ = self._get_applicant_info(detail_id)
            db_info = cv_content.get("db_info", {})
            applicant_data = (
                self.db_manager.get_applicant_by_id(db_info.get("applicant_id"))
                if self.db_manager
                else None
            )

            # --- THE FIX: Convert list of experience strings to list of dicts ---
            job_history_list = extracted_info.get("Experience", [])
            job_history_formatted = [
                {"title": exp, "dates": "N/A"} for exp in job_history_list
            ]

            # Also format education for consistency
            education_list = extracted_info.get("Education", [])
            education_formatted = [
                {"degree": edu, "university": "N/A"} for edu in education_list
            ]

            return {
                "applicant_name": applicant_name,
                "application_role": application_role,
                "birthdate": (
                    str(applicant_data.date_of_birth) if applicant_data else "N/A"
                ),
                "address": applicant_data.address if applicant_data else "N/A",
                "phone_number": (
                    applicant_data.phone_number if applicant_data else "N/A"
                ),
                "skills": extracted_info.get("Skills", []),
                "job_history": job_history_formatted,  # Use the correctly formatted list
                "education": education_formatted,  # Use the correctly formatted list
                "overall_summary": extracted_info.get(
                    "Summary", "No summary available."
                ),
                "cv_path": cv_content["cv_path"],
            }
        except Exception as e:
            print(
                f"[SearchService] EXCEPTION in get_cv_summary for detail_id {detail_id}: {e}"
            )
            traceback.print_exc()
            return {"error": f"Processing error: {str(e)}"}

    def perform_multiple_pattern_search(
        self, patterns: list[str], algorithm: str, num_matches: int
    ) -> Tuple[
        List[Dict[str, Any]], float, float, int, int
    ]:  # Added fuzzy_time and fuzzy_cvs_searched
        exact_start_time = time.time()
        all_cvs = self.cv_data_store.get_all_cvs()
        exact_pattern_matches_dict = {}  # Store by detail_id

        if not all_cvs:
            return [], 0.0, 0.0, 0, 0

        valid_patterns = [p.strip().lower() for p in patterns if p and p.strip()]
        if not valid_patterns:
            return [], 0.0, 0.0, len(all_cvs), 0

        # --- EXACT PATTERN MATCHING PHASE ---
        if algorithm.upper() == "AC":
            try:
                matcher = PatternMatcherFactory.get_matcher("AC")
                for detail_id, cv_data in all_cvs.items():
                    searchable_text = cv_data.get("flat_text", "").lower()
                    if not searchable_text:
                        continue
                    pattern_counts = matcher.count_multiple_patterns(
                        searchable_text, valid_patterns
                    )
                    total_matches = sum(pattern_counts.values())
                    if total_matches > 0:
                        exact_pattern_matches_dict[detail_id] = {
                            "detail_id": detail_id,
                            "cv_path": cv_data.get("cv_path"),
                            "total_matches": total_matches,
                            "matched_keywords": {
                                k: v for k, v in pattern_counts.items() if v > 0
                            },
                            "match_type": "exact_multiple_ac",
                        }
            except ValueError as e:
                print(f"[SearchService] Error creating AC matcher: {e}")
                return [], 0.0, 0.0, len(all_cvs), 0
        else:  # KMP or BM
            try:
                matcher = PatternMatcherFactory.get_matcher(algorithm)
                for detail_id, cv_data in all_cvs.items():
                    searchable_text = cv_data.get("flat_text", "").lower()
                    if not searchable_text:
                        continue
                    current_cv_matches = {}
                    current_cv_total_matches = 0
                    for pattern in valid_patterns:
                        count = matcher.count_occurrences(searchable_text, pattern)
                        if count > 0:
                            current_cv_matches[pattern] = count
                            current_cv_total_matches += count
                    if current_cv_total_matches > 0:
                        exact_pattern_matches_dict[detail_id] = {
                            "detail_id": detail_id,
                            "cv_path": cv_data.get("cv_path"),
                            "total_matches": current_cv_total_matches,
                            "matched_keywords": current_cv_matches,
                            "match_type": f"exact_multiple_{algorithm.lower()}",
                        }
            except ValueError as e:
                print(f"[SearchService] Error creating {algorithm} matcher: {e}")
                return [], 0.0, 0.0, len(all_cvs), 0

        exact_execution_time = time.time() - exact_start_time

        # --- FUZZY MATCHING PHASE for MULTIPLE PATTERNS ---
        fuzzy_start_time = time.time()
        fuzzy_pattern_matches_dict = {}
        num_exact_pattern_found = len(exact_pattern_matches_dict)
        cvs_for_fuzzy_search_multi = {}

        if num_exact_pattern_found < num_matches:
            print(
                f"[SearchService Multi] Found {num_exact_pattern_found} exact pattern matches. Target: {num_matches}. Considering fuzzy search."
            )
            for detail_id, cv_data in all_cvs.items():
                if detail_id not in exact_pattern_matches_dict:
                    cvs_for_fuzzy_search_multi[detail_id] = cv_data

        if cvs_for_fuzzy_search_multi:
            for detail_id, cv_data in cvs_for_fuzzy_search_multi.items():
                flat_text = cv_data.get("flat_text", "")
                if not flat_text:
                    continue

                current_cv_fuzzy_details = {}
                current_cv_fuzzy_score_sum = 0

                for (
                    pattern_term
                ) in valid_patterns:  # Each item in valid_patterns is a keyword/phrase
                    match_info = find_similar_word(
                        pattern_term, flat_text, threshold=0.80
                    )  # Adjust threshold
                    if match_info:
                        best_word, score = match_info
                        current_cv_fuzzy_details[f"{pattern_term} (~{best_word})"] = (
                            f"{int(score*100)}%"
                        )
                        current_cv_fuzzy_score_sum += score

                if current_cv_fuzzy_details:
                    fuzzy_pattern_matches_dict[detail_id] = {
                        "detail_id": detail_id,
                        "cv_path": cv_data.get("cv_path"),
                        "total_matches": current_cv_fuzzy_score_sum,  
                        "matched_keywords": current_cv_fuzzy_details,
                        "match_type": "fuzzy_multiple",
                    }
        fuzzy_execution_time = time.time() - fuzzy_start_time

        combined_results_list_multi = list(exact_pattern_matches_dict.values()) + list(
            fuzzy_pattern_matches_dict.values()
        )

        sorted_cvs_multi = sorted(
            combined_results_list_multi,
            key=lambda x: (
                x.get("match_type", "").startswith("exact"),
                x.get("total_matches", 0),
            ),
            reverse=True,
        )
        top_cvs_multi = sorted_cvs_multi[:num_matches]

        final_results_multi = []
        for cv_match_data in top_cvs_multi:
            applicant_name, application_role, applicant_id_val = (
                self._get_applicant_info(cv_match_data["detail_id"])
            )
            final_results_multi.append(
                {
                    "applicant_id": applicant_id_val,
                    "detail_id": cv_match_data["detail_id"],
                    "applicant_name": applicant_name,
                    "application_role": application_role,
                    "matched_keywords": cv_match_data["matched_keywords"],
                    "total_matches": cv_match_data["total_matches"],
                    "match_type": cv_match_data["match_type"],
                    "cv_path": cv_match_data["cv_path"],
                }
            )

        return (
            final_results_multi,
            exact_execution_time,
            fuzzy_execution_time,
            len(all_cvs),
            len(cvs_for_fuzzy_search_multi),
        )
