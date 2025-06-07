# api/app.py

# This file defines the main backend API server using Flask.
# It establishes the API endpoints that the frontend GUI will communicate with.

from flask import Flask, request, jsonify
from typing import List, Dict, Tuple, Any
from multiprocessing import Value

# Note: In a real application, you would import your actual service and data store classes.
# These imports are placeholders based on your project structure.
# from core.search_service import SearchService
# from core.cv_data_store import CVDataStore
# from core.background_parser import BackgroundParser

# --- Mock/Placeholder Implementations for Demonstration ---
# In the actual implementation, these would be the real classes from your 'core' module.

class MockSearchService:
    """A mock representation of the SearchService."""
    def perform_search(self, keywords: str, algorithm_type: str, num_top_matches: int) -> Tuple[List[Dict[str, Any]], float, float, int, int]:
        print(f"Searching for '{keywords}' using {algorithm_type} (Top {num_top_matches}).")
        
        # Mock exact match results
        exact_results = [
            {
                'applicant_id': 1, 'detail_id': 101, 'applicant_name': 'John Doe',
                'application_role': 'Software Engineer', 'matched_keywords': {'Python': 2, 'Flask': 1},
                'total_matches': 3, 'match_type': 'exact'
            }
        ]
        
        # Mock fuzzy match results (only if exact matches < num_top_matches)
        fuzzy_results = []
        if len(exact_results) < num_top_matches:
            fuzzy_results = [
                {
                    'applicant_id': 2, 'detail_id': 102, 'applicant_name': 'Jane Smith',
                    'application_role': 'Data Scientist', 'matched_keywords': {'Python': 3, 'SQL': 2},
                    'total_matches': 5, 'match_type': 'fuzzy'
                }
            ]
        
        # Combine results
        all_results = exact_results + fuzzy_results[:num_top_matches - len(exact_results)]
        
        exact_cvs_searched = len(exact_results)
        fuzzy_cvs_searched = len(fuzzy_results) if len(exact_results) < num_top_matches else 0
        
        return all_results, 0.05, 0.02, exact_cvs_searched, fuzzy_cvs_searched # results, exact_time, fuzzy_time, exact_cvs_searched, fuzzy_cvs_searched

    def get_cv_summary(self, detail_id):
        print(f"Fetching summary for detail_id: {detail_id}")
        # Mock summary data
        return {
            'applicant_name': 'John Doe', 'birthdate': '1990-01-15', 'address': '123 Tech Lane',
            'phone_number': '555-0101', 'skills': ['Python', 'Flask', 'SQL'],
            'job_history': [{'title': 'Backend Developer', 'dates': '2018-2022'}],
            'education': [{'degree': 'B.S. in Computer Science', 'university': 'Tech University'}],
            'overall_summary': 'Experienced developer with a passion for building scalable web applications.',
            'cv_path': f'data/category_A/cv_{detail_id}.pdf'
        }

class MockCVDataStore:
    """A mock representation of the CVDataStore."""
    def get_parsing_status(self):
        # This would be updated by the background parser.
        # Using multiprocessing.Value for a thread-safe-like counter.
        # In a real scenario, you might use a more robust state management.
        global parsed_count, total_count
        return {"parsed_count": parsed_count.value, "total_count": total_count.value}

# --- Flask App Initialization ---

app = Flask(__name__)

# --- Global State / In-memory Storage Proxies ---
# In a real application, dependency injection or a more structured
# context management would be preferable to global variables.
search_service = MockSearchService()
cv_data_store = MockCVDataStore()

# Using multiprocessing.Value for simple thread-safe counters for the mock parser status
parsed_count = Value('i', 0)
total_count = Value('i', 150) # Example total

# --- API Endpoints ---

@app.route('/status', methods=['GET'])
def get_status():
    """
    Endpoint to check the status of the initial CV parsing process.
    The frontend will poll this to show progress to the user.
    """
    status = cv_data_store.get_parsing_status()
    # Simulate progress for demonstration
    if status['parsed_count'] < status['total_count']:
        parsed_count.value += 5

    return jsonify(status)

@app.route('/search', methods=['POST'])
def search_cvs():
    """
    Endpoint to perform a search for keywords in the CVs.
    Accepts keywords, search algorithm, and number of matches to return.
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    keywords = data.get('keywords')
    algorithm = data.get('search_algorithm', 'KMP') # Default to KMP
    num_matches = data.get('num_top_matches', 10)

    if not keywords:
        return jsonify({"error": "Keywords are required"}), 400

    # Delegate the core logic to the search service
    results, exact_time, fuzzy_time, exact_cvs_searched, fuzzy_cvs_searched = search_service.perform_search(keywords, algorithm, num_matches)

    response = {
        "search_results": results,
        "execution_times": {
            "exact_match_s": exact_time,
            "fuzzy_match_s": fuzzy_time
        },
        "exact_cvs_searched": exact_cvs_searched,
        "fuzzy_cvs_searched": fuzzy_cvs_searched,
        "summary": f"Exact Match: {exact_cvs_searched} CVs scanned in {exact_time*1000:.0f}ms.\nFuzzy Match: {fuzzy_cvs_searched} CVs scanned in {fuzzy_time*1000:.0f}ms."
    }
    return jsonify(response)

@app.route('/summary/<int:detail_id>', methods=['GET'])
def get_summary(detail_id):
    """
    Endpoint to retrieve the detailed summary of a specific CV.
    This includes extracted info like skills, job history, and education.
    """
    if not detail_id:
        return jsonify({"error": "detail_id is required"}), 400

    # Delegate the logic to the search service
    summary_data = search_service.get_cv_summary(detail_id)

    if not summary_data:
        return jsonify({"error": "Summary not found for the given detail_id"}), 404

    return jsonify(summary_data)

if __name__ == '__main__':
    # This block allows running the API server directly for testing.
    # In the final application, main.py will launch this as a separate process.
    from config import API_HOST, API_PORT
    print(f"Starting API server at http://{API_HOST}:{API_PORT}")
    app.run(host=API_HOST, port=API_PORT, debug=True)
