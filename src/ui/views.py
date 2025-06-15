# src/ui/views.py

# This file contains functions that build the different UI views (pages)
# for the Flet application.

import flet as ft
from typing import Any, Dict
from functools import partial
import math

from src.ui.api_client import ApiClient

# --- UI Configuration ---
GRID_COLUMNS = 3  # You can change this value


def show_loading_view(message: str) -> ft.View:
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


def build_summary_view(page: ft.Page, api_client: ApiClient, detail_id: int) -> ft.View:
    """Builds the detailed CV summary page."""

    response = api_client.get_summary(detail_id)

    if not response:
        return ft.View(
            f"/summary/{detail_id}",
            [
                ft.AppBar(title=ft.Text("Error"), bgcolor=ft.Colors.ON_SURFACE_VARIANT),
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
                        ft.Icons.PERSON_OUTLINED, "Birthdate", response.get("birthdate")
                    ),
                    info_row(
                        ft.Icons.HOME_OUTLINED, "Address", response.get("address")
                    ),
                    info_row(
                        ft.Icons.PHONE_OUTLINED, "Phone", response.get("phone_number")
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

    job_history_items = [
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
        for job in response.get("job_history", [])
    ]
    if not job_history_items:
        job_history_items.append(ft.Text("No job history listed."))

    work_card = ft.Card(
        ft.Container(
            ft.Column(
                [
                    ft.Text("Work Experience", style=ft.TextThemeStyle.TITLE_MEDIUM),
                    *job_history_items,
                    ft.Divider(height=10, color="transparent"),
                    ft.Text(
                        "Summary Overview",
                        style=ft.TextThemeStyle.TITLE_SMALL,
                        weight=ft.FontWeight.BOLD,
                    ),
                    ft.Text(response.get("overall_summary", "N/A"), selectable=True),
                ],
                spacing=10,
            ),
            padding=20,
        )
    )

    education_items = [
        ft.Column(
            [
                ft.Text(edu.get("degree", "N/A"), weight=ft.FontWeight.BOLD),
                ft.Text(edu.get("university", "N/A"), color=ft.Colors.BLUE_GREY_500),
            ],
            spacing=2,
        )
        for edu in response.get("education", [])
    ]
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
                leading=ft.IconButton(
                    icon=ft.Icons.ARROW_BACK, on_click=lambda _: page.go("/")
                ),
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


def build_main_view(
    page: ft.Page, api_client: ApiClient, search_state: Dict
) -> ft.View:
    """Builds the main search page of the application, using persistent state."""

    # Controls are enabled by default, assuming parsing is complete.
    keywords_input = ft.TextField(
        label="Keywords",
        hint_text="e.g., Python, React, SQL",
        border=ft.InputBorder.OUTLINE,
        border_radius=8,
        expand=True,
    )
    algo_dropdown = ft.Dropdown(
        label="Algorithm",
        options=[
            ft.dropdown.Option("KMP"),
            ft.dropdown.Option("BM"),
            ft.dropdown.Option("AC"),
        ],
        value="KMP",
        border_radius=8,
        width=120,
    )
    top_n_input = ft.TextField(label="Top N", value="5", width=90, border_radius=8)
    search_button = ft.FilledButton(text="Search", icon=ft.Icons.SEARCH, height=50)

    results_view = ft.Row(wrap=True, spacing=15, run_spacing=15)
    results_container = ft.Column(
        [results_view], expand=True, scroll=ft.ScrollMode.ADAPTIVE
    )
    summary_text = ft.Text(italic=True, color=ft.Colors.BLUE_GREY_600)

    def on_view_cv_click(e, detail_id):
        """Handle View CV button click - open PDF via backend"""
        pdf_url = f"http://127.0.0.1:5000/view_cv/{detail_id}"
        print(f"[UI] Opening CV: {pdf_url}")

        # For WSL - use Windows browser
        import subprocess
        import os

        if "microsoft" in os.uname().release.lower():  # Detect WSL
            try:
                # Use Windows browser from WSL
                subprocess.run(["cmd.exe", "/c", "start", pdf_url], check=True)
            except:
                print(f"[UI] Could not open browser. Please visit: {pdf_url}")
        else:
            # Normal Linux/Mac
            page.launch_url(pdf_url)

    def _populate_results(response_data):
        """Helper function to build result cards from API response data."""
        results_view.controls.clear()
        if response_data and response_data.get("search_results"):
            summary_text.value = response_data.get("summary", "No performance summary.")

            num_results = len(response_data["search_results"])
            effective_columns = min(GRID_COLUMNS, num_results)
            effective_columns = max(1, effective_columns)

            page_padding = 40
            total_spacing = (effective_columns - 1) * results_view.spacing
            card_width = (
                math.floor(
                    (page.width - page_padding - total_spacing) / effective_columns
                )
                - 15
            )
            i = 0
            for i, result in enumerate(response_data["search_results"]):
                detail_id = result.get("detail_id")
                matched_keywords = result.get("matched_keywords", {})
                keywords_column = ft.Column(spacing=2)
                if matched_keywords:
                    # Using a different variable for inner loop index to avoid confusion
                    for kw_idx, (key, value) in enumerate(matched_keywords.items()):
                        keywords_column.controls.append(
                            ft.Text(
                                f"{kw_idx+1}. {key} ({value})"
                            )  # Assuming 'value' is the count
                        )
                else:
                    keywords_column.controls.append(ft.Text("None"))

                card = ft.Card(
                    ft.Container(
                        ft.Column(
                            [
                                ft.Text(
                                    f"{i + 1}. {result.get('applicant_name', 'N/A')}",  # This line is now correct
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
                                            on_click=lambda e, did=detail_id: on_view_cv_click(
                                                e, did
                                            ),
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
                            spacing=8,
                        ),
                        padding=20,
                        border_radius=10,
                        width=card_width,
                    )
                )
                i = i + 1
                results_view.controls.append(card)
        else:
            results_view.controls.append(
                ft.Column(
                    [
                        ft.Icon(
                            ft.Icons.SEARCH_OFF, size=48, color=ft.Colors.BLUE_GREY_200
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

        page.update()

    def handle_search(e):
        kw, algo, top_n = (
            keywords_input.value,
            algo_dropdown.value,
            int(top_n_input.value),
        )
        if not kw:
            page.snack_bar = ft.SnackBar(
                ft.Text("Keywords are required."), bgcolor=ft.Colors.ERROR
            )
            page.snack_bar.open = True
            page.update()
            return

        # Parse keywords - detect if multiple keywords are provided
        keywords_list = [k.strip().lower() for k in kw.split(",") if k.strip()]
        use_multiple_search = len(keywords_list) > 1

        search_button.disabled = True
        results_view.controls.clear()
        results_view.controls.append(
            ft.Container(
                content=ft.Column(
                    [ft.ProgressRing(), ft.Text("Searching CVs...")],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=10,
                ),
                alignment=ft.alignment.center,
                expand=True,
            )
        )
        summary_text.value = ""
        page.update()

        # Use multiple pattern search if multiple keywords are provided
        if use_multiple_search:
            response = api_client.search_multiple_patterns(
                keywords_list, algo, top_n
            )  # Pass algorithm
            search_type = "multiple"
        else:
            response = api_client.search(kw, algo, top_n)
            search_type = "single"

        search_state["search_type"] = search_type
        search_state["last_response"] = response
        _populate_results(response)
        search_button.disabled = False
        page.update()

    search_button.on_click = handle_search

    if search_state.get("last_response"):
        _populate_results(search_state["last_response"])

    return ft.View(
        "/",
        [
            ft.AppBar(
                title=ft.Text("CV Analyzer"), bgcolor=ft.Colors.ON_SURFACE_VARIANT
            ),
            ft.Column(
                [
                    ft.Text(
                        "Search for candidates", style=ft.TextThemeStyle.HEADLINE_MEDIUM
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
                                "Search Results", style=ft.TextThemeStyle.TITLE_LARGE
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
