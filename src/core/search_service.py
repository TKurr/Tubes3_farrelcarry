# src/core/search_service.py

import time
import os
from typing import List, Dict, Tuple, Any
import traceback  # For detailed error logging

from src.core.cv_data_store import CVDataStore
from src.core.fuzzy_matching import find_similar_word
from src.core.pattern_matching import PatternMatcherFactory

# Import the hybrid extractor
from src.core.pdf_processor import extract_hybrid_info

# Import extract_text_from_pdf if direct extraction fallback is needed in get_cv_summary
# from src.core.pdf_processor import extract_text_from_pdf
# from config import DATA_DIR # If direct PDF reading is a fallback


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
        print(
            f"[SearchService] Performing in-memory search for '{keywords_str}' across {len(all_processed_cvs)} pre-processed CVs..."
        )

        exact_matches = {}
        for detail_id_key, cv_content in all_processed_cvs.items():
            # Use flat_text for searching
            cv_search_text = cv_content.get("flat_text", "")
            if not cv_search_text:
                print(
                    f"[SearchService] Warning: No flat_text for detail_id {detail_id_key}"
                )
                continue

            keyword_counts = {}
            total_matches_for_cv = 0
            for keyword in keywords:
                count = matcher.count_occurrences(cv_search_text, keyword)
                if count > 0:
                    keyword_counts[keyword] = count
                    total_matches_for_cv += count

            if total_matches_for_cv > 0:
                exact_matches[detail_id_key] = {
                    "detail_id": detail_id_key,
                    "cv_path": cv_content[
                        "cv_path"
                    ],  # This is the full path from background_parser
                    "total_matches": total_matches_for_cv,
                    "matched_keywords": keyword_counts,
                    "match_type": "exact",
                }

        exact_end_time = time.time()
        exact_execution_time = exact_end_time - exact_start_time

        # --- 2. FUZZY MATCHING PHASE ---
        fuzzy_start_time = time.time()
        fuzzy_matches = {}
        unmatched_cvs_for_fuzzy_count = 0  # Initialize count

        if len(exact_matches) < num_top_matches:
            print("[SearchService] Not enough exact matches. Starting fuzzy search.")
            unmatched_cvs_for_fuzzy = {
                k: v for k, v in all_processed_cvs.items() if k not in exact_matches
            }
            unmatched_cvs_for_fuzzy_count = len(unmatched_cvs_for_fuzzy)

            for detail_id_key, cv_content in unmatched_cvs_for_fuzzy.items():
                # Use flat_text for fuzzy matching
                flat_text_for_fuzzy = cv_content.get("flat_text", "")
                if not flat_text_for_fuzzy:
                    continue

                fuzzy_keyword_counts = {}
                for keyword in keywords:
                    match = find_similar_word(
                        keyword, flat_text_for_fuzzy, threshold=0.85
                    )
                    if match:
                        best_word, score = match
                        fuzzy_keyword_counts[f"{keyword} (~{best_word})"] = (
                            f"{int(score*100)}%"
                        )
                if fuzzy_keyword_counts:
                    fuzzy_matches[detail_id_key] = {
                        "detail_id": detail_id_key,
                        "cv_path": cv_content[
                            "cv_path"
                        ],  # This is the full path from background_parser
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
        for cv_match_data in top_cvs:
            applicant_name, application_role, applicant_id_val = (
                self._get_applicant_info(cv_match_data["detail_id"])
            )
            final_results.append(
                {
                    "applicant_id": applicant_id_val,
                    "detail_id": cv_match_data["detail_id"],
                    "applicant_name": applicant_name,
                    "application_role": application_role,
                    "matched_keywords": cv_match_data["matched_keywords"],
                    "total_matches": cv_match_data["total_matches"],
                    "match_type": cv_match_data["match_type"],
                    "cv_path": cv_match_data[
                        "cv_path"
                    ],  # This is full path from background_parser
                }
            )
        return (
            final_results,
            exact_execution_time,
            fuzzy_execution_time,
            len(all_processed_cvs),  # Total CVs attempted to process
            unmatched_cvs_for_fuzzy_count,  # CVs considered for fuzzy
        )

    def _get_applicant_info(self, detail_id: int) -> tuple:
        """Helper method to get real applicant information from database."""
        if not self.db_manager:
            # Fallback if no database manager
            # Try to get cv_path from CVDataStore to extract filename for a placeholder name
            cv_entry = self.cv_data_store.get_all_cvs().get(detail_id)
            placeholder_name = "Unknown Applicant"
            if cv_entry and cv_entry.get("cv_path"):
                placeholder_name = (
                    os.path.basename(cv_entry.get("cv_path"))
                    .replace(".pdf", "")
                    .replace("_", " ")
                    .title()
                )

            return placeholder_name, "Unknown Role", detail_id

        try:
            # This could be optimized by fetching only the required application if not already cached
            applications = self.db_manager.get_all_applications()
            application = next(
                (app for app in applications if app.detail_id == detail_id), None
            )
            if not application:
                # Fallback if application not found in DB
                cv_entry = self.cv_data_store.get_all_cvs().get(detail_id)
                placeholder_name = "DB App Not Found"
                if cv_entry and cv_entry.get("cv_path"):
                    placeholder_name = (
                        os.path.basename(cv_entry.get("cv_path"))
                        .replace(".pdf", "")
                        .replace("_", " ")
                        .title()
                    )
                return placeholder_name, "N/A", detail_id

            applicant = self.db_manager.get_applicant_by_id(application.applicant_id)
            if applicant:
                full_name = f"{applicant.first_name} {applicant.last_name}".strip()
                return full_name, application.application_role, applicant.applicant_id
            else:
                # Fallback if applicant not found for the application
                return (
                    "DB Applicant Not Found",
                    application.application_role,
                    application.applicant_id,
                )
        except Exception as e:
            print(
                f"[SearchService] Error in _get_applicant_info for detail_id {detail_id}: {e}"
            )
            cv_entry = self.cv_data_store.get_all_cvs().get(detail_id)
            placeholder_name = "Error Applicant"
            if cv_entry and cv_entry.get("cv_path"):
                placeholder_name = (
                    os.path.basename(cv_entry.get("cv_path"))
                    .replace(".pdf", "")
                    .replace("_", " ")
                    .title()
                )
            return placeholder_name, "Error Role", detail_id

    def get_cv_summary(self, detail_id: int) -> Dict[str, Any]:
        """Retrieves and constructs a detailed summary for a given CV."""
        print(f"[SearchService] Fetching summary for detail_id: {detail_id}")

        if not self.db_manager:
            print(
                f"[SearchService] ERROR: db_manager is not available for detail_id: {detail_id}"
            )
            return {
                "error": "Database manager not available"
            }  # Return a dict with error

        try:
            # Get application details
            applications = (
                self.db_manager.get_all_applications()
            )  # Potentially inefficient, consider fetching one
            application = next(
                (app for app in applications if app.detail_id == detail_id), None
            )

            if not application:
                print(
                    f"[SearchService] ERROR: Application not found in DB for detail_id: {detail_id}"
                )
                return {
                    "error": "Application not found in DB"
                }  # Return a dict with error

            print(
                f"[SearchService] Found application for detail_id {detail_id}: {application.__dict__ if application else 'None'}"
            )

            # Get applicant details
            applicant = self.db_manager.get_applicant_by_id(application.applicant_id)

            if not applicant:
                print(
                    f"[SearchService] ERROR: Applicant not found in DB for applicant_id: {application.applicant_id} (linked to detail_id: {detail_id})"
                )
                return {
                    "error": "Applicant not found in DB"
                }  # Return a dict with error

            print(
                f"[SearchService] Found applicant for detail_id {detail_id}: {applicant.__dict__ if applicant else 'None'}"
            )

            # Get CV content from the data store
            cv_content = self.cv_data_store.get_all_cvs().get(detail_id)

            hybrid_info = {}
            if cv_content and "structured_text" in cv_content:
                structured_cv_text = cv_content["structured_text"]
                if structured_cv_text:
                    hybrid_info = extract_hybrid_info(structured_cv_text)
                    print(
                        f"[SearchService] Hybrid extracted info from structured_text for detail_id {detail_id}: {hybrid_info}"
                    )
                else:
                    print(
                        f"[SearchService] structured_text is empty for detail_id: {detail_id}."
                    )
            else:
                print(
                    f"[SearchService] No structured_text found for detail_id: {detail_id}. CV content from store: {cv_content}"
                )

            # Basic info from DB
            applicant_name_db = f"{applicant.first_name} {applicant.last_name}".strip()
            application_role_db = application.application_role
            birthdate_db = (
                str(applicant.date_of_birth) if applicant.date_of_birth else "N/A"
            )
            address_db = applicant.address or "N/A"
            phone_number_db = applicant.phone_number or "N/A"
            cv_path_db = application.cv_path  # This is just filename from DB

            # Parse skills from hybrid_info
            skills_text = hybrid_info.get("Skills", "No skills available")
            skills_list = (
                [skill.strip() for skill in skills_text.split("\n") if skill.strip()]
                if skills_text and skills_text != "No skills available"
                else ["No skills extracted"]
            )

            # Parse experience from hybrid_info
            experience_data = hybrid_info.get("Experience", [])
            job_history = []
            if isinstance(experience_data, list) and experience_data:
                for exp_item in experience_data:
                    if isinstance(exp_item, dict):
                        job_history.append(
                            {
                                "title": exp_item.get("position", "N/A"),
                                "dates": exp_item.get("date_range", "N/A"),
                            }
                        )
                    else:
                        job_history.append({"title": str(exp_item), "dates": "N/A"})
            if not job_history:
                job_history = [{"title": "No experience found", "dates": "N/A"}]

            # Parse education from hybrid_info
            education_text_or_list = hybrid_info.get("Education", "No education listed")
            education_list = []
            if isinstance(education_text_or_list, str):
                if (
                    education_text_or_list
                    and education_text_or_list != "No education listed"
                ):
                    education_items_str = [
                        edu.strip()
                        for edu in education_text_or_list.split("\n")
                        if edu.strip()
                    ]
                    for item_str in education_items_str:
                        education_list.append({"degree": item_str, "university": "N/A"})
                if not education_list:
                    education_list = [
                        {"degree": "No education found", "university": "N/A"}
                    ]
            elif isinstance(education_text_or_list, list):
                for edu_item in education_text_or_list:
                    if isinstance(edu_item, dict):
                        education_list.append(
                            {
                                "degree": edu_item.get("degree", "N/A"),
                                "university": edu_item.get("institution", "N/A"),
                            }
                        )
                    else:
                        education_list.append(
                            {"degree": str(edu_item), "university": "N/A"}
                        )
                if not education_list:
                    education_list = [
                        {"degree": "No education found", "university": "N/A"}
                    ]
            else:
                education_list = [{"degree": "No education found", "university": "N/A"}]

            summary_payload = {
                "applicant_name": applicant_name_db,
                "birthdate": birthdate_db,
                "address": address_db,
                "phone_number": phone_number_db,
                "application_role": application_role_db,
                "skills": skills_list,
                "job_history": job_history,
                "education": education_list,
                "overall_summary": hybrid_info.get("Summary", "No summary available"),
                "certifications": hybrid_info.get(
                    "Certifications", "No certifications available"
                ),
                "projects": hybrid_info.get("Projects", "No projects listed"),
                "extracted_name": hybrid_info.get("Full Name", "Unknown"),
                "contact_info": hybrid_info.get(
                    "Contact Info", "No contact info found"
                ),
                "cv_path": cv_path_db,
            }
            print(
                f"[SearchService] Successfully prepared summary for detail_id {detail_id}."
            )
            return summary_payload

        except Exception as e:
            print(
                f"[SearchService] EXCEPTION in get_cv_summary for detail_id {detail_id}: {e}"
            )
            traceback.print_exc()
            return {"error": f"Processing error: {str(e)}"}  # Return a dict with error
