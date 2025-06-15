# src/core/cv_data_store.py

# This module defines the CVDataStore class, which is now made more robust
# for multithreading using a threading.Event object.

import threading


class CVDataStore:
    """
    A thread-safe, in-memory data store for CV information.
    It uses a threading.Event to reliably signal when background parsing is complete.
    """

    def __init__(self):
        # The main data dictionary.
        self.cvs = {}

        # A dictionary to track the progress of the initial background parsing.
        self._parsing_status = {
            "progress": 0,
            "total": 0,
        }

        # A lock to protect the status dictionary during updates.
        self._lock = threading.Lock()

        # An Event is a much better tool for signaling completion between threads.
        self.parsing_complete_event = threading.Event()

    def add_cv(
        self,
        detail_id: int,
        cv_path: str,
        flat_text: str,
        structured_text: str,
        db_info: dict,
    ):
        """
        Adds a processed CV to the data store, storing both text versions
        and the pre-fetched database information.
        """
        self.cvs[detail_id] = {
            "cv_path": cv_path,
            "flat_text": flat_text,  # For fast searching
            "structured_text": structured_text,  # For detailed summary extraction
            "db_info": db_info,  # Cached DB data (name, role, etc.)
        }

    def get_all_cvs(self) -> dict:
        """Returns the entire dictionary of processed CVs."""
        return self.cvs

    def get_status(self) -> dict:
        """Returns a copy of the current parsing status in a thread-safe way."""
        with self._lock:
            status = self._parsing_status.copy()

        status["is_done"] = self.parsing_complete_event.is_set()
        return status

    def update_status(self, progress: int, total: int):
        """Updates the parsing progress and sets the completion event when done."""
        with self._lock:
            self._parsing_status["progress"] = progress
            self._parsing_status["total"] = total

        if progress >= total and total > 0:
            if not self.parsing_complete_event.is_set():
                print(
                    f"[CVDataStore] Background parsing has completed ({progress}/{total}). Setting completion event."
                )
                self.parsing_complete_event.set()
