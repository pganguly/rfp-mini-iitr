# rfp-mini-iitr

## Overview

**Agentic RFP Evaluation & Supplier Ranking** is a Streamlit-based application that automates the evaluation of Request for Proposal (RFP) submissions from suppliers. It uses LangGraph for workflow orchestration and advanced scoring logic for intelligent supplier ranking.

## Features

- **Multi-modal Evaluation**: Supports both offline demo mode (mock LLM) and live LLM evaluation via OpenRouter
- **Flexible PDF Extraction**: Choose between PyMuPDF or pypdf libraries for PDF content extraction
- **Criteria-Based Scoring**: Define and weight multiple evaluation criteria with active/inactive toggles
- **LLM-Powered Analysis**: Uses OpenRouter API to leverage advanced language models for intelligent proposal evaluation
- **Deterministic Ranking**: Python-based validation, scoring calculation, peer comparison, and tie-break logic ensures reproducible results
- **Interactive Dashboard**: Built with Streamlit for easy supplier evaluation and result visualization
- **Detailed Scorecards**: View comprehensive evaluation results with scores, risks, warnings, and detailed justifications
- **Data Export**: Download complete evaluation results as JSON for further analysis or reporting

## Project Structure

```
rfp-mini-iitr/
├── streamlit_app.py          # Main Streamlit application
├── app/
│   ├── __init__.py
│   ├── config.py             # Configuration (DB path, model, base URL)
│   ├── db.py                 # Database operations and criteria management
│   ├── models.py             # Pydantic models for data validation
│   ├── orchestrator.py       # Batch evaluation orchestration
│   ├── graph.py              # LangGraph workflow definition
│   ├── llm.py                # LLM integration and prompting
│   ├── pdf_tools.py          # PDF extraction utilities
│   ├── scoring.py            # Scoring logic and normalization
│   └── validation.py         # Input validation and weight verification
└── README.md
```

## Key Components

### `streamlit_app.py`
The main application entry point providing:
- **Criteria Tab**: View and manage active evaluation criteria with weight validation
- **Supplier Input Tab**: Upload supplier RFP PDFs, specify supplier details (name, submission date, experience rating)
- **Leaderboard / Scorecards Tab**: View ranked results with detailed evaluation breakdowns

### `app/graph.py`
Implements the LangGraph-based evaluation workflow orchestrating the complete RFP evaluation pipeline.

**Key Features:**
- **RFPGraphState**: A TypedDict that maintains the complete workflow state including:
  - Inputs: supplier data, database path, evaluation mode (mock/LLM), model config, PDF backend
  - Workflow state: criteria, run ID, extracted suppliers, evaluations, normalized records, ranked results
  
- **Workflow Nodes** (executed in sequential order):
  1. **load_criteria_node**: Loads active criteria from the database and validates that weights sum to 100%
  2. **create_batch_node**: Creates a new RFP run record in the database for batch tracking
  3. **extract_documents_node**: Extracts text content from uploaded supplier PDFs using the specified backend
  4. **evaluate_suppliers_node**: Evaluates each supplier using either mock (demo) or real LLM evaluation
  5. **validate_node**: Normalizes raw LLM evaluations, validates scores against criterion boundaries, and generates warnings/risks
  6. **rank_node**: Ranks suppliers using peer comparison (relative performance index) and deterministic tie-breaking
  7. **persist_node**: Saves all results to the database, marking the run as COMPLETED or FAILED

- **Graph Construction**: Built using LangGraph's StateGraph with deterministic sequential edges (START → load_criteria → create_batch → ... → persist → END)

- **Main API Function**: `evaluate_batch_langgraph()` invokes the compiled graph with initial state and returns the run ID, criteria, and ranked results

### `app/scoring.py`
Implements intelligent scoring normalization, peer-comparison ranking, and tie-breaking logic for final supplier ranking.

**Key Scoring Functions:**

- **`absolute_weighted_score(eval_obj, criteria) → float`**
  - Calculates the raw weighted score for a supplier based on individual criterion scores
  - Formula: `Σ (criterion_score / criterion_max_score) × criterion_weight`
  - Returns a normalized float value rounded to 4 decimal places
  - Handles variable max scores per criterion

- **`rank_suppliers(records, criteria) → list[dict]`**
  - Ranks suppliers using a multi-step process:
    1. **Benchmark Calculation**: For each criterion, establishes the highest valid score observed as the benchmark
    2. **Relative Performance Indexing (PPI)**:
       - Calculates relative performance as `(supplier_score / benchmark) × 100%` for each criterion
       - Handles zero-benchmark edge case by assigning 100% relative performance
       - Weights relative performance by criterion weight: `weighted_relative_sum / total_weight`
    3. **Enrichment**: Augments each record with:
       - absolute_score: Raw weighted score
       - ppi: Peer Performance Index (0-100+ scale)
       - Gap analysis: Score difference from benchmark for each criterion
       - Detailed criteria breakdown with scores, benchmarks, gaps, and justifications
    4. **Deterministic Tie-Breaking**: Sorts suppliers by:
       - PPI (descending) - higher relative performance ranks first
       - Submission date (ascending) - earlier submissions preferred
       - Experience rating (descending) - higher ratings preferred
       - Supplier name (ascending alphabetically) - ensures total determinism
    5. **Rank Assignment**: Assigns final_rank starting from 1

**Scoring Concepts:**
- **Absolute Score**: Weighted sum of normalized criterion scores (0-100 scale)
- **PPI (Peer Performance Index)**: Relative performance vs. the best supplier for each criterion, weighted by importance
- **Benchmarking**: Dynamic baseline set by highest-scoring supplier, enabling fair peer comparison
- **Gap Analysis**: Difference between supplier score and benchmark reveals improvement opportunities

### `app/llm.py`
Handles OpenRouter API integration and LLM-based evaluation of supplier proposals.

### `app/db.py`
Manages SQLite database for criteria storage and persistence.

### `app/pdf_tools.py`
PDF content extraction with support for both PyMuPDF and pypdf backends.

## Usage

1. **Configure Criteria**: Set up evaluation criteria in the database with names, descriptions, weights, and max scores
2. **Upload Proposals**: Upload supplier RFP PDFs via the Streamlit interface
3. **Run Evaluation**: Select evaluation mode (offline demo or OpenRouter LLM), configure API settings, and evaluate
4. **Review Results**: View supplier rankings, detailed scorecards with scores and justifications, risks, and warnings
5. **Export Data**: Download complete evaluation results as JSON

## Configuration

Key configuration in `app/config.py`:
- `DEFAULT_MODEL`: Default LLM model (e.g., `openai/gpt-4o-mini`)
- `OPENROUTER_BASE_URL`: OpenRouter API endpoint
- `DEFAULT_MAX_TEXT_CHARS`: Maximum PDF text extraction length
- `DB_PATH`: SQLite database location

## Technology Stack

- **Streamlit**: Interactive web UI
- **LangGraph**: Workflow orchestration
- **OpenRouter**: LLM API integration
- **Pydantic**: Data validation
- **Pandas**: Data manipulation and display
- **PyMuPDF / pypdf**: PDF processing
- **SQLite**: Criteria and results persistence

## Models

### Criterion
Represents evaluation criteria with:
- criterion_id, name, description
- weight (percentage), max_score
- is_active (toggle on/off)

### CriterionEvaluation
Evaluation result for a criterion:
- score, max_score, justification, evidence

### EvaluationResponse
LLM evaluation output with:
- supplier_name, criteria evaluations, risks, overall_summary

### NormalizedEvaluation
Final normalized evaluation with:
- score normalization, warnings, and tie-break explanations

## Workflow Architecture

The application follows a deterministic, sequential workflow:

```
Load Criteria → Create Batch Run → Extract PDFs → Evaluate Suppliers 
   → Validate & Normalize → Rank Suppliers → Persist Results
```

Each step depends on the previous one, ensuring:
- Consistent state management
- Error handling with proper run status tracking
- Reproducible ranking logic independent of evaluation order

## License

This project was created for educational purposes at IIT Roorkee.
