# src/core/background_parser.py

import os
from typing import List, Dict, Any

from src.core.cv_data_store import CVDataStore
from src.core.pdf_processor import (
    # find_pdf_files, # Keep if fallback is used and needs it
    extract_text_from_pdf,
    format_flat_text,
    format_resume,  # For structured text
    # clean_text # If format_resume or other processing needs it
)

# Assuming DatabaseManager and DB_CONFIG are correctly imported if _get_cvs_from_database uses them
# from databaseManager import DatabaseManager
# from config import DB_CONFIG


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
                    "cv_path": app.cv_path,  # This is the path as stored in DB (e.g., "filename.pdf" or "data/ROLE/filename.pdf")
                    "applicant_id": app.applicant_id,
                    "application_role": app.application_role,
                }
            )
        print(f"[BackgroundParser] Found {len(cv_data)} applications in database")
        return cv_data
    except Exception as e:
        print(f"[BackgroundParser] Database error: {e}")
        print("[BackgroundParser] Falling back to file scanning (if implemented)...")
        # Fallback logic can remain if needed
        mock_db_data = []
        # from src.core.pdf_processor import find_pdf_files # If using fallback
        # from config import DATA_DIR # If find_pdf_files needs it
        # for i, pdf_path_fallback in enumerate(find_pdf_files()):
        #     detail_id = 10000 + i
        #     mock_db_data.append({"detail_id": detail_id, "cv_path": os.path.basename(pdf_path_fallback)})
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
        # cv_path_from_db is the path as stored in the database.
        # It could be "filename.pdf" or "data/ROLE/filename.pdf" or other formats.
        cv_path_from_db = app_data["cv_path"]

        # Determine the actual filename and construct the path to the PDF in the "data/" directory.
        # The physical PDF files are expected to be directly under "data/".
        if "/" in cv_path_from_db:
            # If path is like "data/ACCOUNTANT/10554236.pdf", extract "10554236.pdf"
            cv_filename = cv_path_from_db.split("/")[-1]
        else:
            # If path is already just "10554236.pdf"
            cv_filename = cv_path_from_db

        # The actual path where the PDF file is expected to be located on the filesystem.
        # All PDFs are directly under the "data/" directory.
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

            # Generate structured text for summary extraction (e.g., using format_resume)
            # This text retains newlines and some structure.
            structured_text = format_resume(raw_text)

            # Generate flat text for searching (all lowercase, no punctuation/newlines)
            # Usually, flat_text is derived from raw_text to preserve as much original content as possible before flattening.
            flat_text = format_flat_text(raw_text)

            # Store both versions. The cv_path stored here should be the one used for display/linking,
            # which is cv_full_path_on_disk as it points to the actual file.
            cv_data_store.add_cv(
                detail_id, cv_full_path_on_disk, flat_text, structured_text
            )
        except Exception as e:
            print(f"[BackgroundParser] Error processing {cv_full_path_on_disk}: {e}")

        cv_data_store.update_status(i + 1, total_cvs)

    print("[BackgroundParser] Finished processing all CVs!")
