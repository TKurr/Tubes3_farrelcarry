# src/ui/api_client.py

# This file contains the ApiClient class, which handles all HTTP
# communication with the backend Flask server.

import requests
from typing import Dict, Any, Optional

# We need to import the config from the project's root
from config import API_HOST, API_PORT


class ApiClient:
    def __init__(self):
        self.base_url = f"http://{API_HOST}:{API_PORT}"

    def get_status(self) -> Optional[Dict[str, Any]]:
        try:
            response = requests.get(f"{self.base_url}/status", timeout=1)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"[ApiClient Error] Could not connect: {e}")
            return None

    def search(
        self, keywords: str, algorithm: str, num_matches: int
    ) -> Optional[Dict[str, Any]]:
        payload = {
            "keywords": keywords,
            "search_algorithm": algorithm,
            "num_top_matches": num_matches,
        }
        try:
            response = requests.post(
                f"{self.base_url}/search", json=payload, timeout=300
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"[ApiClient Error] Search failed: {e}")
            return None

    def get_summary(self, detail_id: int) -> Optional[Dict[str, Any]]:
        try:
            response = requests.get(f"{self.base_url}/summary/{detail_id}", timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"[ApiClient Error] Summary request failed: {e}")
            return None

    def search_multiple_patterns(
        self, patterns: list[str], algorithm: str, num_matches: int
    ) -> Optional[Dict[str, Any]]:
        payload = {
            "patterns": patterns,
            "search_algorithm": algorithm,  # Use the selected algorithm
            "num_top_matches": num_matches,
        }
        try:
            response = requests.post(
                f"{self.base_url}/search_multiple", json=payload, timeout=300
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"[ApiClient Error] Multiple pattern search failed: {e}")
            return None
