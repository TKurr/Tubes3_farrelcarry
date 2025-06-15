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
    """
    Orchestrates the search process using pre-processed data from the CVDataStore.
    """

    def __init__(self, cv_data_store: CVDataStore, db_manager=None):
        print("[SearchService] Initialized with CVDataStore and DatabaseManager.")
        self.cv_data_store = cv_data_store
        self.db_manager = db_manager

    def perform_search(
        self, keywords_str: str, algorithm_type: str, num_top_matches: int
    ) -> Tuple[List[Dict[str, Any]], float, float, int, int]:
        """
        Performs a search on the in-memory flat_text data.
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
        """Builds a detailed summary using the pre-processed structured_text of a CV."""
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

    def perform_multiple_pattern_search(self, patterns: list[str], algorithm: str, num_matches: int):
        """
        Performs multiple pattern search using the specified algorithm.
        For AC (Aho-Corasick), uses true multiple pattern matching.
        For KMP/BM, performs individual searches for each pattern.
        """
        from src.core.pattern_matching.pattern_matcher_factory import PatternMatcherFactory
        import time
        
        start_time = time.time()
        
        # Get all CV data
        all_cvs = self.cv_data_store.get_all_cvs()
        results = []
        
        if algorithm.upper() == "AC":
            # Use Aho-Corasick for true multiple pattern matching
            matcher = PatternMatcherFactory.get_matcher("AC")
            
            for detail_id, cv_data in all_cvs.items():
                searchable_text = cv_data["text"].lower()
                
                # Use Aho-Corasick for multiple pattern matching
                pattern_counts = matcher.count_multiple_patterns(searchable_text, patterns)
                
                # Calculate total matches and create result if matches found
                total_matches = sum(pattern_counts.values())
                if total_matches > 0:
                    matched_keywords = {k: v for k, v in pattern_counts.items() if v > 0}
                    
                    # Get real applicant data from database
                    applicant_name, application_role, applicant_id = self._get_applicant_info(detail_id)
                    
                    result = {
                        "applicant_id": applicant_id,
                        "detail_id": detail_id,
                        "applicant_name": applicant_name,
                        "application_role": application_role,
                        "total_matches": total_matches,
                        "matched_keywords": matched_keywords,
                        "match_type": "multiple_pattern_ac",
                        "cv_path": cv_data["cv_path"]
                    }
                    results.append(result)
        
        else:
            # Use KMP or BM for individual pattern searches
            matcher = PatternMatcherFactory.get_matcher(algorithm)
            
            for detail_id, cv_data in all_cvs.items():
                searchable_text = cv_data["text"].lower()
                
                # Search each pattern individually
                matched_keywords = {}
                total_matches = 0
                
                for pattern in patterns:
                    count = matcher.count_occurrences(searchable_text, pattern.lower())
                    if count > 0:
                        matched_keywords[pattern] = count
                        total_matches += count
                
                # Create result if any matches found
                if total_matches > 0:
                    # Get real applicant data from database
                    applicant_name, application_role, applicant_id = self._get_applicant_info(detail_id)
                    
                    result = {
                        "applicant_id": applicant_id,
                        "detail_id": detail_id,
                        "applicant_name": applicant_name,
                        "application_role": application_role,
                        "total_matches": total_matches,
                        "matched_keywords": matched_keywords,
                        "match_type": f"multiple_pattern_{algorithm.lower()}",
                        "cv_path": cv_data["cv_path"]
                    }
                    results.append(result)
        
        # Sort by total matches and return top N
        results.sort(key=lambda x: x["total_matches"], reverse=True)
        execution_time = time.time() - start_time
        
        return results[:num_matches], execution_time, len(all_cvs)