# src/ui/flet_frontend.py

# A simple GUI frontend using the Flet library.
# This version is redesigned with a modern UI/UX approach.

import flet as ft
import requests
import time
from typing import Dict, Any, Optional, List
import os
import sys
import math
from functools import partial

# --- Path Correction & API Client ---
PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
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
                f"{self.base_url}/search", json=payload, timeout=30
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


# --- Flet GUI Application ---


def main_flet_app(page: ft.Page):
    """The main function that builds and manages the Flet GUI."""
    page.title = "CV Analyzer"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.theme = ft.Theme(color_scheme_seed="blue_grey", font_family="Roboto")
    page.window_width = 800
    page.window_height = 900
    page.window_min_width = 600
    page.window_min_height = 800
    page.padding = 0
    
    # --- UI Configuration Constant ---
    # Change this value to adjust the number of columns in the results grid
    GRID_COLUMNS = 3

    api_client = ApiClient(f"http://{API_HOST}:{API_PORT}")

    def show_loading_view(message: str):
        """Displays a full-page loading indicator."""
        return ft.View(
            "/loading",
            [
                ft.Column(
                    [
                        ft.ProgressRing(width=30, height=30, stroke_width=3),
                        ft.Text(message, size=16),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    alignment=ft.MainAxisAlignment.CENTER,
                    expand=True,
                )
            ],
            vertical_alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def build_summary_view(detail_id: int) -> ft.View:
        """Builds the detailed CV summary page."""

        response = api_client.get_summary(detail_id)

        if not response:
            return ft.View(
                f"/summary/{detail_id}",
                [
                    ft.AppBar(
                        title=ft.Text("Error"), bgcolor=ft.Colors.ON_SURFACE_VARIANT
                    ),
                    ft.Text(
                        "Could not retrieve summary for that ID.", color="red", size=18
                    ),
                ],
            )

        def info_row(icon: str, label: str, value: Any):
            return ft.Row(
                [
                    ft.Icon(name=icon, color=ft.Colors.BLUE_GREY_400, size=20),
                    ft.Text(label, weight=ft.FontWeight.BOLD, size=14, width=120),
                    ft.Text(
                        str(value) if value else "N/A",
                        selectable=True,
                        size=14,
                        expand=True,
                    ),
                ],
                spacing=15,
            )

        personal_card = ft.Card(
            ft.Container(
                ft.Column(
                    [
                        info_row(
                            ft.Icons.PERSON_OUTLINED,
                            "Birthdate",
                            response.get("birthdate"),
                        ),
                        info_row(
                            ft.Icons.HOME_OUTLINED, "Address", response.get("address")
                        ),
                        info_row(
                            ft.Icons.PHONE_OUTLINED,
                            "Phone",
                            response.get("phone_number"),
                        ),
                    ]
                ),
                padding=20,
            )
        )

        skills_list = response.get("skills", [])
        skill_chips = (
            [ft.Chip(label=ft.Text(str(skill))) for skill in skills_list]
            if skills_list
            else [ft.Text("No skills listed.")]
        )
        skills_card = ft.Card(
            ft.Container(
                ft.Column(
                    [
                        ft.Text("Skills", style=ft.TextThemeStyle.TITLE_MEDIUM),
                        ft.Row(controls=skill_chips, wrap=True),
                    ]
                ),
                padding=20,
            )
        )

        job_history_items = []
        for job in response.get("job_history", []):
            job_history_items.append(
                ft.Column(
                    [
                        ft.Text(job.get("title", "N/A"), weight=ft.FontWeight.BOLD),
                        ft.Text(
                            f"({job.get('dates', 'N/A')})",
                            italic=True,
                            color=ft.Colors.BLUE_GREY_500,
                        ),
                    ],
                    spacing=2,
                )
            )
        if not job_history_items:
            job_history_items.append(ft.Text("No job history listed."))

        work_card = ft.Card(
            ft.Container(
                ft.Column(
                    [
                        ft.Text(
                            "Work Experience", style=ft.TextThemeStyle.TITLE_MEDIUM
                        ),
                        *job_history_items,
                        ft.Divider(height=10, color="transparent"),
                        ft.Text(
                            "Summary Overview",
                            style=ft.TextThemeStyle.TITLE_SMALL,
                            weight=ft.FontWeight.BOLD,
                        ),
                        ft.Text(
                            response.get("overall_summary", "N/A"), selectable=True
                        ),
                    ],
                    spacing=10,
                ),
                padding=20,
            )
        )

        education_items = []
        for edu in response.get("education", []):
            education_items.append(
                ft.Column(
                    [
                        ft.Text(edu.get("degree", "N/A"), weight=ft.FontWeight.BOLD),
                        ft.Text(
                            edu.get("university", "N/A"), color=ft.Colors.BLUE_GREY_500
                        ),
                    ],
                    spacing=2,
                )
            )
        if not education_items:
            education_items.append(ft.Text("No education history listed."))

        education_card = ft.Card(
            ft.Container(
                ft.Column(
                    [
                        ft.Text("Education", style=ft.TextThemeStyle.TITLE_MEDIUM),
                        *education_items,
                    ],
                    spacing=10,
                ),
                padding=20,
            )
        )

        return ft.View(
            f"/summary/{detail_id}",
            [
                ft.AppBar(
                    title=ft.Text(response.get("applicant_name", "CV Summary")),
                    bgcolor=ft.Colors.ON_SURFACE_VARIANT,
                ),
                ft.Column(
                    [personal_card, skills_card, work_card, education_card],
                    spacing=15,
                    scroll=ft.ScrollMode.ADAPTIVE,
                    expand=True,
                ),
            ],
            padding=20,
            bgcolor=ft.Colors.BLUE_GREY_50,
        )

    def build_main_view() -> ft.View:
        """Builds the main search page of the application."""

        keywords_input = ft.TextField(
            label="Keywords",
            hint_text="e.g., Python, React, SQL",
            border=ft.InputBorder.OUTLINE,
            border_radius=8,
            expand=True,
        )
        algo_dropdown = ft.Dropdown(
            label="Algorithm",
            options=[ft.dropdown.Option("KMP"), ft.dropdown.Option("BM")],
            value="KMP",
            border_radius=8,
            width=120,
        )
        top_n_input = ft.TextField(label="Top N", value="5", width=90, border_radius=8)
        search_button = ft.FilledButton(text="Search", icon=ft.Icons.SEARCH, height=50)
        
        # Using a Row with wrap=True for a responsive grid with auto-height cards
        results_view = ft.Row(
            wrap=True,
            spacing=15,
            run_spacing=15,
            # The scroll will be handled by the parent Column
        )

        # Container for the results_view to make it scrollable
        results_container = ft.Column(
            [results_view], 
            expand=True, 
            scroll=ft.ScrollMode.ADAPTIVE
        )

        summary_text = ft.Text(italic=True, color=ft.Colors.BLUE_GREY_600)

        def handle_search(e):
            print("[GUI] Search button clicked.")
            kw = keywords_input.value
            algo = algo_dropdown.value
            top_n = int(top_n_input.value)

            if not kw:
                page.snack_bar = ft.SnackBar(
                    ft.Text("Keywords are required."), bgcolor=ft.Colors.ERROR
                )
                page.snack_bar.open = True
                page.update()
                return

            search_button.disabled = True
            results_view.controls.clear()
            
            loading_container = ft.Container(
                content=ft.Column(
                    [ft.ProgressRing(), ft.Text("Searching CVs...")],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=10,
                ),
                alignment=ft.alignment.center,
                expand=True
            )
            results_view.controls.append(loading_container)
            summary_text.value = ""
            page.update()

            response = api_client.search(kw, algo, top_n)

            results_view.controls.clear()
            if response and response.get("search_results"):
                summary_text.value = response.get("summary", "No performance summary.")
                
                num_results = len(response["search_results"])
                effective_columns = min(GRID_COLUMNS, num_results)
                effective_columns = max(1, effective_columns) 

                page_padding = 40 
                total_spacing = (effective_columns - 10) * results_view.spacing
                
                # --- BUG FIX ---
                # Use math.floor and subtract 1 pixel as a safety margin to prevent wrapping issues.
                card_width = math.floor((page.width - page_padding - total_spacing) / effective_columns) - 60


                for result in response["search_results"]:
                    detail_id = result.get("detail_id")
                    
                    matched_keywords = result.get('matched_keywords', {})
                    keywords_column = ft.Column(spacing=2)
                    if matched_keywords:
                        for i, (key, value) in enumerate(matched_keywords.items()):
                            keywords_column.controls.append(
                                ft.Text(f"{i+1}. {key} ({value} matches)")
                            )
                    else:
                        keywords_column.controls.append(ft.Text("None"))


                    card = ft.Card(
                        ft.Container(
                            ft.Column(
                                [
                                    ft.Text(
                                        f"{result.get('applicant_name', 'N/A')}",
                                        style=ft.TextThemeStyle.TITLE_MEDIUM,
                                        weight=ft.FontWeight.BOLD,
                                    ),
                                    ft.Text(
                                        f"Role: {result.get('application_role', 'N/A')}",
                                        color=ft.Colors.BLUE_GREY_700,
                                    ),
                                    ft.Divider(height=5, color="transparent"),
                                    ft.Row(
                                        [
                                            ft.Icon(
                                                ft.Icons.CHECK_CIRCLE_OUTLINED,
                                                color=ft.Colors.GREEN_500,
                                                size=16,
                                            ),
                                            ft.Text(
                                                f"Total Matches: {result.get('total_matches', 0)}",
                                                size=14,
                                            ),
                                            ft.Icon(ft.Icons.TAG, size=16),
                                            ft.Text(
                                                f"Match Type: {result.get('match_type', 'N/A')}",
                                                size=14,
                                            ),
                                        ],
                                        spacing=5,
                                    ),
                                    ft.Divider(height=10),
                                    ft.Text("Keywords Matched:", weight=ft.FontWeight.BOLD),
                                    keywords_column,
                                    ft.Container(expand=True),
                                    ft.Row(
                                        [
                                            ft.OutlinedButton(
                                                "View CV",
                                                icon=ft.Icons.PICTURE_AS_PDF_OUTLINED,
                                                on_click=lambda e, p=result.get('cv_path'): print(f"View CV clicked for path: {p}")
                                            ),
                                            ft.FilledButton(
                                                "View Summary",
                                                icon=ft.Icons.VISIBILITY_OUTLINED,
                                                on_click=partial(
                                                    lambda _, did: page.go(
                                                        f"/summary/{did}"
                                                    ),
                                                    did=detail_id,
                                                ),
                                            ),
                                        ],
                                        alignment=ft.MainAxisAlignment.END,
                                    ),
                                ],
                                spacing=8
                            ),
                            padding=20,
                            border_radius=10,
                            width=card_width 
                        )
                    )
                    results_view.controls.append(card)
            else:
                results_view.controls.append(
                    ft.Column(
                        [
                            ft.Icon(
                                ft.Icons.SEARCH_OFF,
                                size=48,
                                color=ft.Colors.BLUE_GREY_200,
                            ),
                            ft.Text(
                                "No results found.",
                                style=ft.TextThemeStyle.HEADLINE_SMALL,
                                color=ft.Colors.BLUE_GREY_400,
                            ),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    )
                )

            search_button.disabled = False
            page.update()

        search_button.on_click = handle_search

        return ft.View(
            "/",
            [
                ft.AppBar(
                    title=ft.Text("CV Analyzer"), bgcolor=ft.Colors.ON_SURFACE_VARIANT
                ),
                ft.Column(
                    [
                        ft.Text(
                            "Search for candidates",
                            style=ft.TextThemeStyle.HEADLINE_MEDIUM,
                        ),
                        ft.Row(
                            [keywords_input, algo_dropdown, top_n_input],
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        search_button,
                        ft.Divider(height=20),
                        ft.Row(
                            [
                                ft.Text(
                                    "Search Results",
                                    style=ft.TextThemeStyle.TITLE_LARGE,
                                ),
                                summary_text,
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                        results_container, 
                    ],
                    spacing=15,
                    expand=True,
                ),
            ],
            padding=20,
            bgcolor=ft.Colors.BLUE_GREY_50,
        )

    # --- Router for multi-page navigation ---
    def route_change(route):
        page.views.clear()

        if page.route == "/":
            page.views.append(build_main_view())
        elif page.route.startswith("/summary/"):
            detail_id = int(page.route.split("/")[-1])
            page.views.append(build_summary_view(detail_id))
        else:  # Initial loading or unknown route
            page.views.append(show_loading_view("Preparing Application..."))

        page.update()

    def view_pop(view):
        page.views.pop()
        top_view = page.views[-1]
        page.go(top_view.route)

    page.on_route_change = route_change
    page.on_view_pop = view_pop

    # --- Initial application startup ---
    def check_backend_status():
        """Polls the backend and enables the UI when ready."""
        while True:
            if api_client.get_status():
                print("[GUI] Backend is ready. Loading main view.")
                page.go("/")
                break
            else:
                print("[GUI] Waiting for backend...")
            time.sleep(1)

    page.go("/loading")  # Start on the loading screen
    page.run_thread(check_backend_status)


def start_gui(use_web_browser: bool = False):
    """Launches the Flet application."""
    print("[Main] Launching Flet GUI application...")
    view_mode = ft.WEB_BROWSER if use_web_browser else ft.FLET_APP
    ft.app(target=main_flet_app, view=view_mode, assets_dir="assets")
