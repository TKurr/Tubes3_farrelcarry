# src/core/background_parser.py

# This module contains the worker function for the background parsing thread.
# It populates the CVDataStore upon application startup.

import os
from typing import List, Dict, Any

from src.core.cv_data_store import CVDataStore
from src.core.pdf_processor import (
    find_pdf_files,
    extract_text_from_pdf,
    format_flat_text,
)


def _get_cvs_from_database() -> List[Dict[str, Any]]:
    """
    MOCK FUNCTION: Simulates fetching application details from a database
    by dynamically scanning the data directory for all available PDF files.
    """
    print("[BackgroundParser] MOCK: Dynamically scanning for CVs...")
    mock_db_data = []
    for i, pdf_path in enumerate(find_pdf_files()):
        detail_id = 101 + i
        mock_db_data.append({"detail_id": detail_id, "cv_path": pdf_path})
    return mock_db_data


def parsing_thread_worker(cv_data_store: CVDataStore):
    """
    This function is the target for the background thread.
    It finds, processes, and stores all CVs in the CVDataStore.
    """
    print("[BackgroundParser] Starting background PDF processing thread...")

    applications = _get_cvs_from_database()
    total_cvs = len(applications)
    cv_data_store.update_status(0, total_cvs)

    if total_cvs == 0:
        print("[BackgroundParser] No CVs found to process.")
        cv_data_store.update_status(0, 0)  # Mark as done
        return

    for i, app_data in enumerate(applications):
        detail_id = app_data["detail_id"]
        pdf_path = app_data["cv_path"]

        print(
            f"[BackgroundParser] Processing CV {i + 1}/{total_cvs}: {os.path.basename(pdf_path)}"
        )

        raw_text = extract_text_from_pdf(pdf_path)
        flat_text = format_flat_text(raw_text)

        cv_data_store.add_cv(detail_id, pdf_path, flat_text)
        cv_data_store.update_status(i + 1, total_cvs)
