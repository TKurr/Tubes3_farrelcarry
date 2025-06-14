# api/app.py

# This file defines the main backend API server using Flask.
# It now manages a background thread for pre-processing all PDFs on startup.

import threading
from flask import Flask, request, jsonify

# --- Real Service and Data Store Imports ---
from src.core.search_service import SearchService
from src.core.cv_data_store import CVDataStore
from src.core.background_parser import parsing_thread_worker

# --- Flask App Initialization ---
app = Flask(__name__)

# --- Singleton Data Store ---
# This single instance will be shared across the application.
cv_data_store = CVDataStore()

# --- Service Instantiation ---
# The SearchService is given the shared data store instance.
search_service = SearchService(cv_data_store=cv_data_store)

# --- Background Parsing Initialization ---
parser_thread = None
parsing_started = False


def ensure_parsing_started():
    """Ensure background parsing is started (called on first request)."""
    global parser_thread, parsing_started
    if not parsing_started:
        print("[API] Starting background parsing thread...")
        parser_thread = threading.Thread(
            target=parsing_thread_worker, args=(cv_data_store,), daemon=True
        )
        parser_thread.start()
        parsing_started = True


# --- API Endpoints ---


@app.route("/status", methods=["GET"])
def get_status():
    """
    Endpoint to check the status of the initial CV parsing process.
    Reads the status directly from the thread-safe CVDataStore.
    """
    ensure_parsing_started()  # Start parsing on first request
    return jsonify(cv_data_store.get_status())


@app.route("/search", methods=["POST"])
def search_cvs():
    """
    Endpoint to perform a search. It delegates all logic to the SearchService.
    The guard clause is now robustly thread-safe.
    """
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
    """Endpoint to retrieve the detailed summary of a specific CV."""
    ensure_parsing_started()  # Start parsing on first request

    if not detail_id:
        return jsonify({"error": "detail_id is required"}), 400

    summary_data = search_service.get_cv_summary(detail_id)
    if not summary_data:
        return jsonify({"error": "Summary not found for the given detail_id"}), 404

    return jsonify(summary_data)


if __name__ == "__main__":
    from config import API_HOST, API_PORT

    print(f"Starting API server at http://{API_HOST}:{API_PORT}")
    app.run(host=API_HOST, port=API_PORT, debug=False)
