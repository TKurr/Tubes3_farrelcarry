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
        self.cvs = {}

        self._parsing_status = {
            "progress": 0,
            "total": 0,
        }

        self._lock = threading.Lock()

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
        return self.cvs

    def get_status(self) -> dict:
        """Returns a copy of the current parsing status in a thread-safe way."""
        with self._lock:
            print(f"[CVDataStore] get_status() INSIDE lock: _parsing_status = {self._parsing_status}")
            
            progress = self._parsing_status["progress"]
            total = self._parsing_status["total"]
            
            is_done = self.parsing_complete_event.is_set()
            
            if is_done and total > 0:
                progress = total
                self._parsing_status["progress"] = total  
            
            status = {
                "parsed_count": progress,
                "total_count": total,
                "progress": progress,      # Keep for backward compatibility
                "total": total,
                "is_done": is_done
            }
        
        # Debug logging
        print(f"[CVDataStore] get_status() returning: parsed={progress}, total={total}, is_done={is_done}")
        
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
