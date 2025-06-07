# src/ui/flet_frontend.py

# A simple GUI frontend using the Flet library.
# This replaces the CLI frontend and resolves the input handling issues
# associated with multiprocessing.

import flet as ft
import requests
import time
from typing import Dict, Any, Optional
import os
import sys

# --- Path Correction & API Client ---
# This setup is to ensure we can import the config and use the ApiClient.
# In a larger app, ApiClient might be in its own file.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(PROJECT_ROOT)
from config import API_HOST, API_PORT

class ApiClient:
    """Handles all communication with the backend API."""
    def __init__(self, base_url: str):
        self.base_url = base_url

    def get_status(self) -> Optional[Dict[str, Any]]:
        try:
            response = requests.get(f"{self.base_url}/status", timeout=1)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"[ApiClient Error] Could not connect: {e}")
            return None

    def search(self, keywords: str, algorithm: str, num_matches: int) -> Optional[Dict[str, Any]]:
        payload = {"keywords": keywords, "search_algorithm": algorithm, "num_top_matches": num_matches}
        try:
            response = requests.post(f"{self.base_url}/search", json=payload, timeout=30)
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

# --- Flet GUI Application ---

def main_flet_app(page: ft.Page):
    """The main function that builds the Flet GUI."""
    page.title = "Applicant Tracking System"
    page.vertical_alignment = ft.MainAxisAlignment.START
    page.window_width = 600
    page.window_height = 800

    api_client = ApiClient(f"http://{API_HOST}:{API_PORT}")

    # --- UI Components ---
    status_text = ft.Text("Connecting to backend...", style=ft.TextThemeStyle.HEADLINE_SMALL)
    status_progress = ft.ProgressBar(width=400, value=0)
    
    keywords_input = ft.TextField(label="Keywords", hint_text="e.g., Python, React, SQL")
    algo_dropdown = ft.Dropdown(
        label="Algorithm",
        options=[
            ft.dropdown.Option("KMP"),
            ft.dropdown.Option("BM"),
        ],
        value="KMP"
    )
    top_n_input = ft.TextField(label="Top N Matches", value="5", width=150)
    search_button = ft.ElevatedButton(text="Search", icon=ft.Icons.SEARCH)
    
    results_view = ft.ListView(expand=1, spacing=10, auto_scroll=True)
    summary_text = ft.Text(style=ft.TextThemeStyle.BODY_SMALL, selectable=True)

    summary_id_input = ft.TextField(label="Detail ID for Summary", width=200)
    summary_button = ft.ElevatedButton(text="Get Summary")

    def handle_search(e):
        """Event handler for the Search button."""
        print("[GUI] Search button clicked.")
        kw = keywords_input.value
        algo = algo_dropdown.value
        top_n = int(top_n_input.value)

        if not kw:
            results_view.controls.clear()
            results_view.controls.append(ft.Text("Error: Keywords are required.", color="red"))
            page.update()
            return

        # Show loading indicator
        search_button.disabled = True
        results_view.controls.clear()
        results_view.controls.append(ft.ProgressRing())
        summary_text.value = "Searching..."
        page.update()

        response = api_client.search(kw, algo, top_n)
        
        results_view.controls.clear() # Clear loading ring
        if response and response.get("search_results"):
            summary_text.value = response.get("summary", "No performance summary.")
            for result in response["search_results"]:
                card = ft.Card(
                    content=ft.Container(
                        padding=10,
                        content=ft.Column([
                            ft.Text(f"{result.get('applicant_name', 'N/A')} (Role: {result.get('application_role', 'N/A')})", style=ft.TextThemeStyle.TITLE_MEDIUM),
                            ft.Text(f"Detail ID: {result.get('detail_id', 'N/A')} | Total Matches: {result.get('total_matches', 'N/A')}"),
                            ft.Text(f"Keywords: {result.get('matched_keywords', {})}")
                        ])
                    )
                )
                results_view.controls.append(card)
        else:
            results_view.controls.append(ft.Text("No results found or an error occurred."))
            summary_text.value = ""

        search_button.disabled = False
        page.update()

    def handle_get_summary(e):
        """Event handler for the Get Summary button."""
        print("[GUI] Get Summary button clicked.")
        try:
            detail_id = int(summary_id_input.value)
            response = api_client.get_summary(detail_id)
            if response:
                summary_info = "\n--- CV Summary ---\n" + "\n".join([f"{key}: {value}" for key, value in response.items()])
                summary_text.value = summary_info
            else:
                summary_text.value = "Could not retrieve summary for that ID."
        except (ValueError, TypeError):
            summary_text.value = "Error: Please enter a valid numerical Detail ID."
        page.update()


    search_button.on_click = handle_search
    summary_button.on_click = handle_get_summary

    # --- Initial Status Check ---
    def check_backend_status():
        while True:
            status = api_client.get_status()
            if status:
                parsed = status.get("parsed_count", 0)
                total = status.get("total_count", 1) # Avoid division by zero
                
                status_text.value = f"Backend Parsing: {parsed}/{total}"
                status_progress.value = parsed / total if total > 0 else 0
                
                if parsed >= total:
                    status_text.value = "Backend Ready!"
                    status_progress.visible = False
                    # Enable search controls
                    keywords_input.disabled = False
                    algo_dropdown.disabled = False
                    top_n_input.disabled = False
                    search_button.disabled = False
                    page.update()
                    break # Exit the loop
            else:
                status_text.value = "Backend is unavailable. Retrying..."

            page.update()
            time.sleep(0.2)
    
    # --- Page Layout ---
    page.add(
        status_text,
        status_progress,
        ft.Row(controls=[keywords_input, algo_dropdown, top_n_input]),
        search_button,
        ft.Divider(),
        ft.Text("Search Results", style=ft.TextThemeStyle.HEADLINE_SMALL),
        results_view,
        ft.Divider(),
        summary_text,
        ft.Row(controls=[summary_id_input, summary_button])
    )

    # Disable controls until backend is ready
    keywords_input.disabled = True
    algo_dropdown.disabled = True
    top_n_input.disabled = True
    search_button.disabled = True
    page.update()

    # Start the background status checker in a new thread
    page.run_thread(check_backend_status)


def start_gui():
    """Launches the Flet application."""
    print("[Main] Launching Flet GUI application...")
    ft.app(target=main_flet_app)

