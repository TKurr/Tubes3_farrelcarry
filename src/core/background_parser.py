# src/core/background_parser.py

# This module contains the worker function for the background parsing thread.
# It populates the CVDataStore upon application startup.

import os
from typing import List, Dict, Any

from src.core.cv_data_store import CVDataStore
from src.core.pdf_processor import (
    find_pdf_files,
    extract_pdf_text,
    format_flat_text,
)


def _get_cvs_from_database(db_manager) -> List[Dict[str, Any]]:
    """
    REAL FUNCTION: Fetches application details from the MySQL database.
    Falls back to file scanning if the database connection fails.
    """
    print("[BackgroundParser] Fetching CV applications from database...")
    if not db_manager:
        print(
            "[BackgroundParser] No db_manager provided. Falling back to file scanning..."
        )
        mock_db_data = []
        for i, pdf_path in enumerate(find_pdf_files()):
            detail_id = 101 + i
            mock_db_data.append(
                {
                    "detail_id": detail_id,
                    "cv_path": pdf_path,
                    "applicant_id": detail_id,
                    "application_role": "Unknown Role",
                }
            )
        return mock_db_data

    try:
        applications = db_manager.get_all_applications()
        cv_data = [
            {
                "detail_id": app.detail_id,
                "cv_path": app.cv_path,
                "applicant_id": app.applicant_id,
                "application_role": app.application_role,
            }
            for app in applications
        ]
        print(f"[BackgroundParser] Found {len(cv_data)} applications in database")
        return cv_data
    except Exception as e:
        print(f"[BackgroundParser] Database error: {e}")
        return []


def parsing_thread_worker(cv_data_store: CVDataStore, db_manager):
    """
    This function is the target for the background thread.
    It now processes and stores both flat and structured text for each CV.
    """
    print("[BackgroundParser] Starting background PDF processing thread...")
    applications = _get_cvs_from_database(db_manager)
    total_cvs = len(applications)
    cv_data_store.update_status(0, total_cvs)

    if total_cvs == 0:
        print("[BackgroundParser] No CVs found to process.")
        cv_data_store.update_status(0, 0)
        return

    for i, app_data in enumerate(applications):
        detail_id, cv_path = app_data["detail_id"], app_data["cv_path"]
        cv_full_path = os.path.join("data", os.path.basename(cv_path))

        print(
            f"[BackgroundParser] Processing CV {i + 1}/{total_cvs}: {os.path.basename(cv_full_path)}"
        )
        if not os.path.exists(cv_full_path):
            print(
                f"[BackgroundParser] WARNING: File not found: {cv_full_path}, skipping."
            )
            cv_data_store.update_status(i + 1, total_cvs)
            continue

        try:
            # The raw text contains all the structure needed for summary extraction
            raw_text = extract_pdf_text(cv_full_path)
            # The flat text is for efficient, simple keyword searching
            flat_text = format_flat_text(raw_text)

            db_info = {
                "applicant_id": app_data.get("applicant_id"),
                "application_role": app_data.get("application_role"),
            }
            # The raw_text is now stored as 'structured_text'
            cv_data_store.add_cv(detail_id, cv_full_path, flat_text, raw_text, db_info)
        except Exception as e:
            print(f"[BackgroundParser] Error processing {cv_full_path}: {e}")

        cv_data_store.update_status(i + 1, total_cvs)

    print("[BackgroundParser] Finished processing all CVs!")
