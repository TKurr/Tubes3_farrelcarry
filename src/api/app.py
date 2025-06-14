# api/app.py

# This file defines the main backend API server using Flask.
# It establishes the API endpoints that the frontend GUI will communicate with.

from flask import Flask, request, jsonify
from multiprocessing import Value

# --- Real Service Import ---
# We now import the actual SearchService instead of using a mock class here.
from src.core.search_service import SearchService

# In a real app, these would also be real classes.
# from src.core.cv_data_store import CVDataStore
# from src.core.background_parser import BackgroundParser


# --- Placeholder for demonstration ---
class MockCVDataStore:
    """A mock representation of the CVDataStore."""

    def get_parsing_status(self):
        global parsed_count, total_count
        return {"parsed_count": parsed_count.value, "total_count": total_count.value}


# --- Flask App Initialization ---
app = Flask(__name__)

# --- Service Instantiation ---
# In a full-fledged application, you would manage the lifecycle of these
# objects more formally, possibly using a dependency injection framework.
# For now, we instantiate our service and its (mock) dependencies here.

# TODO: Replace mock dependencies with real ones as they are built.
# cv_data_store = CVDataStore()
# search_service = SearchService(cv_data_store=cv_data_store, ...)
cv_data_store = MockCVDataStore()
search_service = SearchService()  # The real service class


# Using multiprocessing.Value for simple thread-safe counters for the mock parser status
parsed_count = Value("i", 0)
total_count = Value("i", 150)  # Example total

# --- API Endpoints ---


@app.route("/status", methods=["GET"])
def get_status():
    """
    Endpoint to check the status of the initial CV parsing process.
    The frontend will poll this to show progress to the user.
    """
    status = cv_data_store.get_parsing_status()
    # Simulate progress for demonstration
    if status["parsed_count"] < status["total_count"]:
        parsed_count.value += 5

    return jsonify(status)


@app.route("/search", methods=["POST"])
def search_cvs():
    """
    Endpoint to perform a search for keywords in the CVs.
    Delegates all logic to the SearchService.
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    keywords = data.get("keywords")
    algorithm = data.get("search_algorithm", "KMP")
    num_matches = data.get("num_top_matches", 10)

    if not keywords:
        return jsonify({"error": "Keywords are required"}), 400

    # Delegate the core logic to the real search service
    results, exact_time, fuzzy_time, exact_cvs_searched, fuzzy_cvs_searched = (
        search_service.perform_search(keywords, algorithm, num_matches)
    )

    response = {
        "search_results": results,
        "execution_times": {"exact_match_s": exact_time, "fuzzy_match_s": fuzzy_time},
        "exact_cvs_searched": exact_cvs_searched,
        "fuzzy_cvs_searched": fuzzy_cvs_searched,
        "summary": f"Exact Match: {exact_cvs_searched} CVs scanned in {exact_time*1000:.2f}ms. | Fuzzy Match: {fuzzy_cvs_searched} CVs scanned in {fuzzy_time*1000:.2f}ms.",
    }
    return jsonify(response)


@app.route("/summary/<int:detail_id>", methods=["GET"])
def get_summary(detail_id):
    """
    Endpoint to retrieve the detailed summary of a specific CV.
    Delegates all logic to the SearchService.
    """
    if not detail_id:
        return jsonify({"error": "detail_id is required"}), 400

    # Delegate the logic to the real search service
    summary_data = search_service.get_cv_summary(detail_id)

    if not summary_data:
        return jsonify({"error": "Summary not found for the given detail_id"}), 404

    return jsonify(summary_data)


if __name__ == "__main__":
    # This block allows running the API server directly for testing.
    from config import API_HOST, API_PORT

    print(f"Starting API server at http://{API_HOST}:{API_PORT}")
    app.run(host=API_HOST, port=API_PORT, debug=True)
