import os
from typing import List, Dict, Any

from src.core.cv_data_store import CVDataStore
from src.core.pdf_processor import (
    find_pdf_files,
    extract_text_from_pdf,
    format_flat_text,
)


def _get_cvs_from_database(db_manager) -> List[Dict[str, Any]]:
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
        print("[BackgroundParser] Falling back to file scanning...")

        mock_db_data = []
        for i, pdf_path in enumerate(find_pdf_files()):
            detail_id = 101 + i
            mock_db_data.append({"detail_id": detail_id, "cv_path": pdf_path})
        return mock_db_data


def parsing_thread_worker(cv_data_store: CVDataStore, db_manager):
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
        cv_filename = app_data["cv_path"] 

        # Construct the full path
        cv_full_path = os.path.join("data", cv_filename)

        print(f"[BackgroundParser] Processing CV {i + 1}/{total_cvs}: {cv_filename}")

        # Check if file exists
        if not os.path.exists(cv_full_path):
            print(f"[BackgroundParser] WARNING: File not found: {cv_full_path}")
            cv_data_store.update_status(i + 1, total_cvs)
            continue

        try:
            raw_text = extract_text_from_pdf(cv_full_path)
            flat_text = format_flat_text(raw_text)

            # Store with the full path for later use
            cv_data_store.add_cv(detail_id, cv_full_path, flat_text)
        except Exception as e:
            print(f"[BackgroundParser] Error processing {cv_full_path}: {e}")

        cv_data_store.update_status(i + 1, total_cvs)

    print("[BackgroundParser] Finished processing all CVs!")
