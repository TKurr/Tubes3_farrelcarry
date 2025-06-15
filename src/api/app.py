import threading
import sys
import os
from flask import Flask, request, jsonify, send_file


from src.core.search_service import SearchService
from src.core.cv_data_store import CVDataStore
from src.core.background_parser import parsing_thread_worker
from src.core.pdf_processor import extract_hybrid_info


sys.path.append(os.path.join(os.path.dirname(__file__), "..", "core"))
from src.core.databaseManager import DatabaseManager
from config import DB_CONFIG


app = Flask(__name__)

cv_data_store = CVDataStore()

# Initialize DatabaseManager singleton
database_manager = DatabaseManager(
    host=DB_CONFIG["host"],
    user=DB_CONFIG["user"],
    password=DB_CONFIG["password"],
    database=DB_CONFIG["database"],
)


search_service = SearchService(cv_data_store=cv_data_store, db_manager=database_manager)


parser_thread = None
parsing_started = False


def ensure_parsing_started():
    """Ensure background parsing is started (called on first request)."""
    global parser_thread, parsing_started
    if not parsing_started:
        print("[API] Starting background parsing thread...")
        parser_thread = threading.Thread(
            target=parsing_thread_worker,
            args=(cv_data_store, database_manager),
            daemon=True,
        )
        parser_thread.start()
        parsing_started = True


# --- API Endpoints ---


@app.route("/status", methods=["GET"])
def get_status():
    ensure_parsing_started()  # Start parsing on first request
    return jsonify(cv_data_store.get_status())


@app.route("/search", methods=["POST"])
def search_cvs():
    ensure_parsing_started()  # Start parsing on first request

    # Check the thread-safe event to see if parsing is complete.
    if not cv_data_store.parsing_complete_event.is_set():
        return (
            jsonify(
                {"error": "Server is still processing CVs. Please try again shortly."}
            ),
            503,
        )

    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    keywords = data.get("keywords")
    algorithm = data.get("search_algorithm", "KMP")
    num_matches = data.get("num_top_matches", 10)

    if not keywords:
        return jsonify({"error": "Keywords are required"}), 400

    results, exact_time, fuzzy_time, exact_cvs, fuzzy_cvs = (
        search_service.perform_search(keywords, algorithm, num_matches)
    )

    response = {
        "search_results": results,
        "execution_times": {"exact_match_s": exact_time, "fuzzy_match_s": fuzzy_time},
        "exact_cvs_searched": exact_cvs,
        "fuzzy_cvs_searched": fuzzy_cvs,
        "summary": f"Exact Match: {exact_cvs} CVs scanned in {exact_time*1000:.2f}ms. | Fuzzy Match: {fuzzy_cvs} CVs scanned in {fuzzy_time*1000:.2f}ms.",
    }
    return jsonify(response)


@app.route("/summary/<int:detail_id>", methods=["GET"])
def get_summary(detail_id):
    ensure_parsing_started()  # Start parsing on first request

    if not detail_id:
        return jsonify({"error": "detail_id is required"}), 400

    summary_data = search_service.get_cv_summary(detail_id)
    if not summary_data:
        return jsonify({"error": "Summary not found for the given detail_id"}), 404

    return jsonify(summary_data)


@app.route("/search_multiple", methods=["POST"])
def search_multiple_patterns():
    ensure_parsing_started()

    if not cv_data_store.parsing_complete_event.is_set():
        return (
            jsonify(
                {"error": "Server is still processing CVs. Please try again shortly."}
            ),
            503,
        )

    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    patterns = data.get("patterns", [])
    algorithm = data.get("search_algorithm", "KMP")
    num_matches = data.get("num_top_matches", 10)

    if not patterns or not isinstance(patterns, list):
        return jsonify({"error": "Patterns list is required"}), 400

    valid_patterns = [p.strip() for p in patterns if p and p.strip()]
    if not valid_patterns:
        return jsonify({"error": "At least one valid pattern is required"}), 400

    # CORRECTED: Unpack 5 values
    results, exact_time, fuzzy_time, total_cvs_processed, fuzzy_cvs_searched = (
        search_service.perform_multiple_pattern_search(
            valid_patterns, algorithm, num_matches
        )
    )

    response = {
        "search_results": results,
        "execution_times": {"exact_match_s": exact_time, "fuzzy_match_s": fuzzy_time},
        "exact_cvs_searched": total_cvs_processed,  # Assuming exact search always scans all
        "fuzzy_cvs_searched": fuzzy_cvs_searched,
        "summary": f"Multi-Pattern ({algorithm}): Exact scan on {total_cvs_processed} CVs in {exact_time*1000:.2f}ms. Fuzzy scan on {fuzzy_cvs_searched} CVs in {fuzzy_time*1000:.2f}ms.",
    }
    return jsonify(response)


if __name__ == "__main__":
    from config import API_HOST, API_PORT

    print(f"Starting API server at http://{API_HOST}:{API_PORT}")
    app.run(host=API_HOST, port=API_PORT, debug=False)


@app.route("/view_cv/<int:detail_id>", methods=["GET"])
def view_cv(detail_id):
    """Serve PDF file for viewing in browser"""
    try:
        # Get the CV path from database
        applications = database_manager.get_all_applications()
        application = next(
            (app for app in applications if app.detail_id == detail_id), None
        )

        if not application:
            return jsonify({"error": "CV not found"}), 404

        cv_path = application.cv_path

        # Extract just the filename, removing any role directory
        if "/" in cv_path:
            cv_filename = cv_path.split("/")[-1]  # Extract filename
        else:
            cv_filename = cv_path

        # Construct path directly in data/ - go up 3 levels from src/api/app.py to project root
        project_root = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        absolute_cv_path = os.path.join(project_root, "data", cv_filename)

        print(f"[Flask] Looking for PDF at: {absolute_cv_path}")  # Debug line

        if not os.path.exists(absolute_cv_path):
            return jsonify({"error": f"PDF file not found: {absolute_cv_path}"}), 404

        return send_file(
            absolute_cv_path, as_attachment=False, mimetype="application/pdf"
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500
