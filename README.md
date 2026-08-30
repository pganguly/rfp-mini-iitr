# rfp-mini-iitr

## Overview

**Agentic RFP Evaluation & Supplier Ranking** is a Streamlit-based application that automates the evaluation of Request for Proposal (RFP) submissions from suppliers. It uses LangGraph for workflow orchestration, LLM-powered evaluation via OpenRouter, and deterministic Python for validation, scoring, peer comparison, tie-breaking, and final ranking.

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

### `app/llm.py`
Handles OpenRouter API integration and LLM-based evaluation of supplier proposals.

### `app/scoring.py`
Implements scoring normalization, peer comparison, and tie-breaking logic for final ranking.

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

## License

This project was created for educational purposes at IIT Roorkee.
