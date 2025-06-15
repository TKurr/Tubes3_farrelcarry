# CV Search Application with Pattern Matching Algorithms

A comprehensive CV search application that implements multiple string matching algorithms (KMP, Boyer-Moore, and Aho-Corasick) to efficiently search through resume databases. The application features a modern GUI built with Flet and a robust backend API for processing PDF documents and performing pattern matching operations.

## Overview

This application demonstrates the practical implementation of three fundamental string matching algorithms:

### Algorithms Implemented

#### 1. KMP (Knuth-Morris-Pratt) Algorithm
The KMP algorithm uses a preprocessing step to create a "failure function" that helps skip characters during pattern matching. It achieves O(n + m) time complexity by avoiding redundant comparisons when a mismatch occurs. The algorithm is particularly efficient for patterns with repeating substrings.

#### 2. Boyer-Moore Algorithm  
The Boyer-Moore algorithm searches from right to left within the pattern and uses two heuristics: the bad character rule and the good suffix rule. This implementation focuses on the bad character heuristic, which can skip multiple characters when a mismatch occurs, making it very fast for large alphabets and long patterns.

#### 3. Aho-Corasick Algorithm
The Aho-Corasick algorithm is designed for multiple pattern matching. It builds a trie structure with failure links, allowing it to find all occurrences of multiple patterns in a single pass through the text. This makes it extremely efficient when searching for multiple keywords simultaneously.

## Features

- **Multi-Algorithm Support**: Choose between KMP, Boyer-Moore, or Aho-Corasick algorithms
- **PDF Processing**: Automatic extraction and processing of text from PDF resumes
- **Multiple Pattern Search**: Search for multiple keywords simultaneously (optimized with Aho-Corasick)
- **Modern GUI**: User-friendly interface built with Flet framework
- **Database Integration**: MySQL/MariaDB backend for storing applicant information
- **Performance Metrics**: Real-time execution time measurements and comparison
- **REST API**: Full-featured API for programmatic access

## System Requirements

### Software Dependencies
- **Python 3.10+**
- **MySQL/MariaDB Server**
- **Operating System**: Windows, macOS, or Linux

### Python Dependencies
```
flet>=0.10.0
flask>=2.3.0
requests>=2.31.0
mysql-connector-python>=8.1.0
pdfplumber>=0.9.0
pytesseract>=0.3.10
Pillow>=10.0.0
Faker>=19.0.0
```

## Installation

### 1. Clone the Repository
```bash
git clone <repository-url>
cd Tubes3
```

### 2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Database Setup
1. Install and start MySQL/MariaDB server
2. Update database configuration in `src/config.py`:
```python
DB_CONFIG = {
    "host": "localhost",
    "user": "your_username",
    "password": "your_password",
    "database": "cvApplicationDatabase"
}
```

3. Initialize the database:
```bash
cd src/core
python test.py
```

### 5. Prepare CV Data
Place PDF resume files in the `data/` directory. The application will automatically process these files during startup.

## Usage

### Running the Application

#### Start the Complete Application (GUI + API)
```bash
cd src
python main.py
```

## Project Structure

```
Tubes3/
├── src/
│   ├── main.py                 # Application entry point
│   ├── config.py              # Configuration settings
│   ├── api/
│   │   └── app.py             # Flask API server
│   ├── ui/
│   │   ├── flet_frontend.py   # Main GUI application
│   │   ├── views.py           # GUI views and components
│   │   └── api_client.py      # API client for GUI
│   ├── core/
│   │   ├── pattern_matching/
│   │   │   ├── kmp_algorithm.py
│   │   │   ├── boyer_moore_algorithm.py
│   │   │   ├── aho_corasick_algorithm.py
│   │   │   └── pattern_matcher_factory.py
│   │   ├── search_service.py  # Search orchestration
│   │   ├── cv_data_store.py   # In-memory data management
│   │   ├── pdf_processor.py   # PDF text extraction
│   │   └── databaseManager.py # Database operations
│   └── database/
│       └── database.sql       # Database schema and seed data
├── data/                      # PDF resume files
└── README.md
```

## Performance Comparison

The application provides real-time performance metrics for each algorithm:

- **KMP**: Consistent O(n + m) performance, excellent for most use cases
- **Boyer-Moore**: Superior performance on large texts with long patterns
- **Aho-Corasick**: Unmatched efficiency for multiple pattern searches

## Authors

**Team Members:**
- Muhammad Farrel Wibowo - *13523153*
- Theo Kurniadi - *13523154*
- I Made Wiweka Putera - *13523160*

## Acknowledgments

- Course: Strategi Algoritma (Algorithm Strategy)
- Institution: Institut Teknologi Bandung
- Semester: 4
- Special thanks to course instructors and teaching assistants

---