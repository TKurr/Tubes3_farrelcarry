# src/ui/flet_frontend.py

# This is the main controller for the Flet application. It handles routing,
# app state, and orchestrates the UI by calling view-building functions.

import flet as ft
import time

# Import the refactored components
from src.ui.api_client import ApiClient
from src.ui.views import build_main_view, build_summary_view, show_loading_view


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

    api_client = ApiClient()

    # State dictionary to hold search results across view changes
    search_state = {"last_response": None}

    # --- Router for multi-page navigation ---
    def route_change(route):
        page.views.clear()

        if page.route == "/":
            # Pass the search state to the main view builder
            page.views.append(build_main_view(page, api_client, search_state))
        elif page.route.startswith("/summary/"):
            detail_id = int(page.route.split("/")[-1])
            page.views.append(build_summary_view(page, api_client, detail_id))
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
