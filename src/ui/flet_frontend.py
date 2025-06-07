import flet as ft
import requests
import time
from typing import Dict, Any, Optional
import os
import sys

# --- Path Correction & API Client ---
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

    def build_summary_page(detail_id: int):
        page.controls.clear()
        page.update()

        response = api_client.get_summary(detail_id)
        print(detail_id)
        print(response)

        if not response:
            page.controls.append(ft.Text("Could not retrieve summary for that ID.", color="red"))
            page.update()
            return

        def label_text(label, value):
            return ft.Row([
                ft.Text(f"{label}:", weight=ft.FontWeight.BOLD, width=120),
                ft.Text(str(value) if value else "N/A", selectable=True, expand=True)
            ])

        # Header
        header = ft.Text("CV Summary", style=ft.TextThemeStyle.HEADLINE_MEDIUM, weight=ft.FontWeight.BOLD)

        # Identitas
        identitas_card = ft.Card(
            elevation=2,
            content=ft.Container(
                border_radius=10,
                padding=15,
                content=ft.Column([
                    ft.Text(response.get("applicant_name", "N/A"), size=20, weight=ft.FontWeight.BOLD),
                    ft.Text(f"Birthdate: {response.get('birthdate', 'N/A')}"),
                    ft.Text(f"Address: {response.get('address', 'N/A')}"),
                    ft.Text(f"Phone Number: {response.get('phone_number', 'N/A')}"),
                ])
            )
        )

        # Skills
        skills_list = response.get("skills", [])
        if isinstance(skills_list, list) and skills_list:
            skill_chips = [
                ft.Container(
                    content=ft.Chip(label=ft.Text(str(skill))),
                    padding=5
                )
                for skill in skills_list
            ]
            skills_section = ft.Column([
                ft.Text("Skills:", weight=ft.FontWeight.BOLD),
                ft.Row(
                    controls=skill_chips,
                    run_spacing=10,
                    spacing=10
                )
            ])
        else:
            skills_section = ft.Text("Skills: N/A", weight=ft.FontWeight.BOLD)

        skills_card = ft.Card(
            content=ft.Container(
                padding=10,
                border_radius=10,
                content=skills_section
            )
        )

        # Job History
        job_history_texts = []
        for job in response.get("job_history", []):
            dates = job.get("dates", "N/A")
            title = job.get("title", "N/A")
            job_history_texts.append(ft.Text(f"{dates} - {title}"))

        job_history = ft.Card(
            content=ft.Container(
                border_radius=10,
                padding=10,
                content=ft.Column([
                    ft.Text("Job History:", weight=ft.FontWeight.BOLD),
                    *job_history_texts,
                    ft.Text(response.get("overall_summary", "N/A"))
                ])
            )
        )

        # Education
        education_data = response.get("education", [])
        if education_data and isinstance(education_data, list) and isinstance(education_data[0], dict):
            degree = education_data[0].get("degree", "N/A")
            university = education_data[0].get("university", "N/A")
        else:
            degree = "N/A"
            university = "N/A"

        education_texts = []
        for edu in response.get("education", []):
            dates = job.get("degree", "N/A")
            title = job.get("university", "N/A")
            education_texts.append(ft.Text(f"{degree} - {university}"))

        education = ft.Card(
            content=ft.Container(
                border_radius=10,
                padding=10,
                content=ft.Column([
                    ft.Text("Education:", weight=ft.FontWeight.BOLD),
                    *education_texts,
                ])
            )
        )

        back_button = ft.ElevatedButton("Back", on_click=lambda e: build_main_page())

        page.controls.append(
            ft.Column(
                [
                    header,
                    ft.Divider(),
                    identitas_card,
                    ft.Divider(),
                    skills_card,
                    ft.Divider(),
                    job_history,
                    ft.Divider(),
                    education,
                    ft.Divider(),
                    back_button
                ],
                scroll=ft.ScrollMode.AUTO,
                spacing=20,
                alignment=ft.MainAxisAlignment.START,
                expand=True
            )
        )
        page.update()


    def handle_search(e):
        print("[GUI] Search button clicked.")
        kw = keywords_input.value
        algo = algo_dropdown.value
        top_n = int(top_n_input.value)

        if not kw:
            results_view.controls.clear()
            results_view.controls.append(ft.Text("Error: Keywords are required.", color="red"))
            page.update()
            return

        search_button.disabled = True
        results_view.controls.clear()
        results_view.controls.append(ft.ProgressRing())
        summary_text.value = "Searching..."
        page.update()

        response = api_client.search(kw, algo, top_n)

        results_view.controls.clear()
        if response and response.get("search_results"):
            summary_text.value = response.get("summary", "No performance summary.")
            for result in response["search_results"]:
                detail_id = result.get('detail_id', None)
                
                summary_btn = ft.ElevatedButton(
                    "Summary",
                    on_click=lambda e, did=detail_id: build_summary_page(did)
                )
                card = ft.Card(
                    content=ft.Container(
                        padding=10,
                        content=ft.Column([
                            ft.Text(f"{result.get('applicant_name', 'N/A')} (Role: {result.get('application_role', 'N/A')})", style=ft.TextThemeStyle.TITLE_MEDIUM),
                            ft.Text(f"Detail ID: {detail_id} | Total Matches: {result.get('total_matches', 'N/A')}"),
                            ft.Text(f"Keywords: {result.get('matched_keywords', {})}"),
                            summary_btn
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

    # --- Initial Status Check ---
    def check_backend_status():
        while True:
            status = api_client.get_status()
            if status:
                parsed = status.get("parsed_count", 0)
                total = status.get("total_count", 1) 
                
                status_text.value = f"Backend Parsing: {parsed}/{total}"
                status_progress.value = parsed / total if total > 0 else 0
                
                if parsed >= total:
                    status_text.value = "CV Analyzer App"
                    status_progress.visible = False
                    keywords_input.disabled = False
                    algo_dropdown.disabled = False
                    top_n_input.disabled = False
                    search_button.disabled = False
                    page.update()
                    break 
            else:
                status_text.value = "Backend is unavailable. Retrying..."

            page.update()
            time.sleep(0.2)
    
    def build_main_page():
        page.controls.clear()
        page.add(
            status_text,
            status_progress,
            ft.Divider(),
            ft.Row(controls=[keywords_input, algo_dropdown, top_n_input, search_button]),
            ft.Divider(),
            ft.Text("Search Results", style=ft.TextThemeStyle.HEADLINE_SMALL),
            results_view,
            ft.Divider(),
            summary_text,
        )
        page.update()
    
    build_main_page()

    # Disable control sampe pasing selsai
    keywords_input.disabled = True
    algo_dropdown.disabled = True
    top_n_input.disabled = True
    search_button.disabled = True
    page.update()

    # Cek status background di thread lain
    page.run_thread(check_backend_status)


def start_gui():
    print("[Main] Launching Flet GUI application...")
    ft.app(target=main_flet_app)

