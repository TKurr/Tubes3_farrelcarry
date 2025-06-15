import flet as ft
import time


from src.ui.api_client import ApiClient
from src.ui.views import build_main_view, build_summary_view


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


    search_state = {"last_response": None}

    def build_initial_loading_view() -> ft.View:
        progress_bar = ft.ProgressBar(width=400, value=0)
        status_text = ft.Text("Connecting to backend...")

        def check_backend_status():
            print("[GUI] Started polling for backend status...")
            
            while True:
                status = api_client.get_status()
                if status:
                    parsed = status.get("parsed_count", 0)
                    total = status.get("total_count", 1)
                    is_done = status.get("is_done", False)
                    

                    status_text.value = f"Parsing CVs: {parsed} / {total}"
                    progress_bar.value = parsed / total if total > 0 else 0
                    
                    print(f"[GUI] Status: {parsed}/{total}, is_done: {is_done}")  # Debug log
                    

                    page.update()
                    

                    if is_done:
                        print("[GUI] Backend reported parsing is complete. Navigating to main view.")
                        page.go("/")
                        break
                else:
                    status_text.value = "Backend is unavailable. Retrying..."
                    page.update()
                

                time.sleep(1)

            print("[GUI] Backend reported parsing is complete. Navigating to main view.")
            page.go("/")

        page.run_thread(check_backend_status)

        return ft.View(
            "/loading",
            [
                ft.Column(
                    [
                        ft.Text("CV Analyzer", style=ft.TextThemeStyle.DISPLAY_SMALL),
                        ft.Text(
                            "Initializing...",
                            style=ft.TextThemeStyle.HEADLINE_SMALL,
                            color=ft.Colors.BLUE_GREY_400,
                        ),
                        ft.Divider(height=30, color="transparent"),
                        progress_bar,
                        status_text,
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    alignment=ft.MainAxisAlignment.CENTER,
                    expand=True,
                    spacing=10,
                )
            ],
        )

    # --- Router for multi-page navigation ---
    def route_change(route):
        page.views.clear()

        if page.route == "/":
            page.views.append(build_main_view(page, api_client, search_state))
        elif page.route.startswith("/summary/"):
            page.views.append(
                build_summary_view(page, api_client, int(page.route.split("/")[-1]))
            )
        else:
            page.views.append(build_initial_loading_view())

        page.update()

    def view_pop(view):
        page.views.pop()
        top_view = page.views[-1]
        page.go(top_view.route)

    page.on_route_change = route_change
    page.on_view_pop = view_pop


    page.go("/loading")


def start_gui(use_web_browser: bool = False):
    """Launches the Flet application."""
    print("[Main] Launching Flet GUI application...")
    view_mode = ft.WEB_BROWSER if use_web_browser else ft.FLET_APP
    ft.app(target=main_flet_app, view=view_mode, assets_dir="assets")
