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

    def add_cv(self, detail_id: int, cv_path: str, text: str):
        self.cvs[detail_id] = {"cv_path": cv_path, "text": text}

    def get_all_cvs(self) -> dict:
        return self.cvs

    def get_status(self) -> dict:
        print(f"[CVDataStore] get_status() called on instance: {id(self)}")
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
        print(f"[CVDataStore] update_status() called on instance: {id(self)}")
        print(f"[CVDataStore] update_status BEFORE lock: progress={progress}, total={total}")
        
        with self._lock:
            print(f"[CVDataStore] update_status INSIDE lock BEFORE update: stored_progress={self._parsing_status['progress']}, stored_total={self._parsing_status['total']}")
            
            self._parsing_status["progress"] = progress
            self._parsing_status["total"] = total
            
            print(f"[CVDataStore] update_status INSIDE lock AFTER update: stored_progress={self._parsing_status['progress']}, stored_total={self._parsing_status['total']}")
            
            # Check completion condition inside the lock
            should_complete = progress >= total and total > 0
        
        # Debug logging
        print(f"[CVDataStore] update_status({progress}/{total}) - should_complete: {should_complete}")
        
        # Set the event outside the lock to avoid deadlock
        if should_complete and not self.parsing_complete_event.is_set():
            print(f"[CVDataStore] Background parsing has completed ({progress}/{total}). Setting completion event.")
            self.parsing_complete_event.set()