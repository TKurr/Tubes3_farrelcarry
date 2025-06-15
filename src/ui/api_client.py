# src/ui/api_client.py

# This file contains the ApiClient class, which handles all HTTP
# communication with the backend Flask server.

import requests
from typing import Dict, Any, Optional

# We need to import the config from the project's root
from config import API_HOST, API_PORT


class ApiClient:
    """Handles all communication with the backend API."""

    def __init__(self):
        self.base_url = f"http://{API_HOST}:{API_PORT}"

    def get_status(self) -> Optional[Dict[str, Any]]:
        """Polls the /status endpoint to get parsing progress."""
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
        """Sends a search request to the /search endpoint."""
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
        """Fetches a detailed CV summary from the /summary/<id> endpoint."""
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
        """Sends a multiple pattern search request with specified algorithm."""
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
