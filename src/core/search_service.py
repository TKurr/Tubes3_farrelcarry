# src/core/search_service.py

# This file contains the SearchService class, which now operates on
# pre-processed, in-memory data for maximum performance.

import time
import os
from typing import List, Dict, Tuple, Any

from src.core.cv_data_store import CVDataStore
from src.core.fuzzy_matching import find_similar_word
from src.core.pattern_matching import PatternMatcherFactory


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

        # --- 4. BUILD FINAL RESPONSE WITH REAL DATABASE DATA ---
        final_results = []
        for cv in top_cvs:
            # Get real applicant data from database
            applicant_name, application_role, applicant_id = self._get_applicant_info(
                cv["detail_id"]
            )

            final_results.append(
                {
                    "applicant_id": applicant_id,
                    "detail_id": cv["detail_id"],
                    "applicant_name": applicant_name,
                    "application_role": application_role,
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

    def _get_applicant_info(self, detail_id: int) -> tuple:
        """Helper method to get real applicant information from database."""
        if not self.db_manager:
            # Fallback to filename if no database
            return "Unknown Applicant", "Unknown Role", detail_id

        try:
            # Get application details
            applications = self.db_manager.get_all_applications()
            application = next(
                (app for app in applications if app.detail_id == detail_id), None
            )

            if not application:
                return "Unknown Applicant", "Unknown Role", detail_id

            # Get applicant details
            applicant = self.db_manager.get_applicant_by_id(application.applicant_id)

            if applicant:
                full_name = f"{applicant.first_name} {applicant.last_name}".strip()
                return full_name, application.application_role, applicant.applicant_id
            else:
                return (
                    "Unknown Applicant",
                    application.application_role,
                    application.applicant_id,
                )

        except Exception as e:
            print(
                f"[SearchService] Error getting applicant info for detail_id {detail_id}: {e}"
            )
            # Fallback to filename
            return "Unknown Applicant", "Unknown Role", detail_id

    def get_cv_summary(self, detail_id: int) -> Dict[str, Any]:
        """Retrieves and constructs a detailed summary for a given CV."""
        print(f"[SearchService] Fetching summary for detail_id: {detail_id}")

        if not self.db_manager:
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

        try:
            # Get application details
            applications = self.db_manager.get_all_applications()
            application = next(
                (app for app in applications if app.detail_id == detail_id), None
            )

            if not application:
                return {"error": "Application not found"}

            # Get applicant details
            applicant = self.db_manager.get_applicant_by_id(application.applicant_id)

            if not applicant:
                return {"error": "Applicant not found"}

            return {
                "applicant_name": f"{applicant.first_name} {applicant.last_name}",
                "birthdate": (
                    str(applicant.date_of_birth) if applicant.date_of_birth else "N/A"
                ),
                "address": applicant.address or "N/A",
                "phone_number": applicant.phone_number or "N/A",
                "application_role": application.application_role,
                "skills": ["Skills extraction not implemented yet"],
                "job_history": [],
                "education": [],
                "overall_summary": "Summary extraction not implemented yet. Requires RegexExtractor.",
                "cv_path": application.cv_path,
            }

        except Exception as e:
            print(
                f"[SearchService] Error getting CV summary for detail_id {detail_id}: {e}"
            )
            return {"error": f"Database error: {str(e)}"}

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