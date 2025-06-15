# src/core/cv_data_store.py

import threading


class CVDataStore:
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
        self.cvs[detail_id] = {
            "cv_path": cv_path,
            "flat_text": flat_text,  
            "structured_text": structured_text,  
            "db_info": db_info,  
        }

    def get_all_cvs(self) -> dict:
        return self.cvs

    def get_status(self) -> dict:
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
                "progress": progress,     
                "total": total,
                "is_done": is_done
            }
        
        # Debug logging
        print(f"[CVDataStore] get_status() returning: parsed={progress}, total={total}, is_done={is_done}")
        
        return status

    def update_status(self, progress: int, total: int):
        with self._lock:
            self._parsing_status["progress"] = progress
            self._parsing_status["total"] = total

        if progress >= total and total > 0:
            if not self.parsing_complete_event.is_set():
                print(
                    f"[CVDataStore] Background parsing has completed ({progress}/{total}). Setting completion event."
                )
                self.parsing_complete_event.set()
