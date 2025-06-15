# src/core/background_parser.py

import os
from typing import List, Dict, Any
import traceback  # For detailed error logging

from src.core.cv_data_store import CVDataStore
from src.core.pdf_processor import (
    extract_text_from_pdf, 
    format_flat_text,
)


def _get_cvs_from_database(db_manager) -> List[Dict[str, Any]]:
    """
    REAL FUNCTION: Fetches application details from the MySQL database.
    """
    print("[BackgroundParser] Fetching CV applications from database...")
    try:
        applications = db_manager.get_all_applications()
        cv_data = []
        for app in applications:
            cv_data.append(
                {
                    "detail_id": app.detail_id,
                    "cv_path": app.cv_path,
                    "applicant_id": app.applicant_id,
                    "application_role": app.application_role,
                }
            )
        print(f"[BackgroundParser] Found {len(cv_data)} applications in database")
        return cv_data
    except Exception as e:
        print(f"[BackgroundParser] Database error: {e}")
        print("[BackgroundParser] Falling back to file scanning (if implemented)...")
        mock_db_data = []
        return mock_db_data


def parsing_thread_worker(cv_data_store: CVDataStore, db_manager):
    """
    This function is the target for the background thread.
    It finds, processes, and stores all CVs in the CVDataStore.
    """
    print("[BackgroundParser] Starting background PDF processing thread...")

    applications = _get_cvs_from_database(db_manager)
    total_cvs = len(applications)
    cv_data_store.update_status(0, total_cvs)

    if total_cvs == 0:
        print("[BackgroundParser] No CVs found to process.")
        cv_data_store.update_status(0, 0)  # Mark as done
        return

    for i, app_data in enumerate(applications):
        detail_id = app_data["detail_id"]
        cv_path_from_db = app_data["cv_path"]

        if "/" in cv_path_from_db:
            cv_filename = cv_path_from_db.split("/")[-1]
        else:
            cv_filename = cv_path_from_db

        cv_full_path_on_disk = os.path.join("data", cv_filename)

        print(
            f"[BackgroundParser] Processing CV {i + 1}/{total_cvs}: {cv_filename} (DB path: '{cv_path_from_db}', Disk path: '{cv_full_path_on_disk}')"
        )

        if not os.path.exists(cv_full_path_on_disk):
            print(
                f"[BackgroundParser] WARNING: File not found on disk: {cv_full_path_on_disk}"
            )
            cv_data_store.update_status(i + 1, total_cvs)
            continue

        try:
            raw_text = extract_text_from_pdf(cv_full_path_on_disk)

            structured_text = raw_text

            flat_text = format_flat_text(raw_text)

            db_info = {
                "applicant_id": app_data.get("applicant_id"),
                "application_role": app_data.get("application_role"),
            }

            cv_data_store.add_cv(
                detail_id, cv_full_path_on_disk, flat_text, structured_text, db_info
            )
        except Exception as e:
            print(f"[BackgroundParser] Error processing {cv_full_path_on_disk}: {e}")
            traceback.print_exc()

        cv_data_store.update_status(i + 1, total_cvs)

    print("[BackgroundParser] Finished processing all CVs!")
