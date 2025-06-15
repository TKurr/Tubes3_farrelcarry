# src/core/cv_data_store.py

import threading


class CVDataStore:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(CVDataStore, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "_initialized"):  # Prevent re-initialization
            self.cvs = {}
            self._parsing_status = {"progress": 0, "total": 0}
            self._lock = threading.Lock()
            self.parsing_complete_event = threading.Event()
            self._initialized = True

    def add_cv(
        self, detail_id: int, cv_path: str, flat_text: str, structured_text: str
    ):
        """Adds a processed CV to the data store with both flat and structured text."""
        self.cvs[detail_id] = {
            "cv_path": cv_path,
            "flat_text": flat_text,
            "structured_text": structured_text,  # Store the structured text
        }

    def get_all_cvs(self) -> dict:
        """Returns the entire dictionary of processed CVs."""
        return self.cvs

    def get_status(self) -> dict:
        """Returns a copy of the current parsing status in a thread-safe way."""
        # print(f"[CVDataStore] get_status() called on instance: {id(self)}") # Optional debug
        with self._lock:
            # print(f"[CVDataStore] get_status() INSIDE lock: _parsing_status = {self._parsing_status}") # Optional debug
            progress = self._parsing_status["progress"]
            total = self._parsing_status["total"]
            is_done_event = self.parsing_complete_event.is_set()

            if is_done_event and total > 0 and progress < total:
                # If event is set, but progress isn't max, force it for consistency
                # This can happen if the last update_status call was missed by a polling cycle
                progress = total
                # self._parsing_status["progress"] = total # No need to update here, just for return

            status = {
                "parsed_count": progress,
                "total_count": total,
                "progress": progress,
                "total": total,
                "is_done": is_done_event,
            }
        # print(f"[CVDataStore] get_status() returning: parsed={progress}, total={total}, is_done={is_done_event}") # Optional debug
        return status

    def update_status(self, progress: int, total: int):
        """Updates the parsing progress and sets the completion event when done."""
        # print(f"[CVDataStore] update_status() called on instance: {id(self)}") # Optional debug
        # print(f"[CVDataStore] update_status BEFORE lock: progress={progress}, total={total}") # Optional debug
        with self._lock:
            # print(f"[CVDataStore] update_status INSIDE lock BEFORE update: stored_progress={self._parsing_status['progress']}, stored_total={self._parsing_status['total']}") # Optional debug
            self._parsing_status["progress"] = progress
            self._parsing_status["total"] = total
            # print(f"[CVDataStore] update_status INSIDE lock AFTER update: stored_progress={self._parsing_status['progress']}, stored_total={self._parsing_status['total']}") # Optional debug
            should_complete = progress >= total and total > 0

        # print(f"[CVDataStore] update_status({progress}/{total}) - should_complete: {should_complete}") # Optional debug
        if should_complete and not self.parsing_complete_event.is_set():
            print(
                f"[CVDataStore] Background parsing has completed ({progress}/{total}). Setting completion event."
            )
            self.parsing_complete_event.set()
