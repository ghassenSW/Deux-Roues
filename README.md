# Deux Roues Validation API

A precise and structured API service utilizing Google's Gemini LLM architecture to automatically cross-verify Tunisian vehicle transaction documents, specifically targeting Identity Cards (CIN), Sales Contracts/Invoices, and Receipts (Quittances).

## Features
- **Dynamic Multi-Document Verification**: Compares logic between Identity, Contracts, and Receipts natively for variable sets (2 to 4 documents).
- **In-Memory Expected Validations**: Injects user-provided expected data cleanly allowing LLM verification against ground truths.
- **Strict JSON Structuring**: Forges Gemini output into an exact schema combining semantic reasoning branches (`_reasoning_1`, `_reasoning_2`) with boolean evaluations.
- **Rate-limit Resiliency**: Custom `503` and `429` retry logic implementation ensures high availability despite Google Server API demand spikes.
- **FastAPI Backend**: Fully encapsulated REST API endpoints configured and pre-optimized with Uvicorn.
- **Containerized Environment**: Full Docker Compose setup specifically mapping port `8081` to avoid environment clashes.

## Structure Overview
- `main.py`: Core FastAPI file orchestrating endpoints and temporary file processing logic.
- `verifier.py`: Dedicated script initializing the Gemini Client, establishing the `config`, handling PIL images, and wrapping Google Server timeout catches.
- `prompt.py`: Houses the absolute System Prompt. Extracts fields (Name, CIN, Chassis Frame No., Engine Size) and evaluates discrepancies safely.

## Setup Instructions

### 1. Environment Keys
Create an `.env` file at the root of the project directory referencing `.env.example`:
```
GEMINI_API_KEY=your_actual_google_gemini_api_key_here
```

### 2. Running Locally (Without Docker)
Make sure you have an active Virtual Environment. Install requirements carefully:
```bash
pip install -r requirements.txt
```
To run the server:
```bash
uvicorn main:app --host 0.0.0.0 --port 8081
```

### 3. Running via Docker
If Docker Desktop is installed, start the API instantly:
```bash
docker-compose up --build
```
Your server will deploy to `http://localhost:8081`.

## Endpoints
### `POST /api/v1/deux-roues/verify`
Accepts `multipart/form-data` with images matching the internal key `files` and an optional `expected_values` form field.

**Input**:
- `files`: 2-4 image documents (.jpg, .png) under Form Data.
- `expected_values` (Optional): A stringified JSON providing the ground truth to match against. Ex: `{"Nom Prénom":"Doe", "CIN Number":"12345678", "Numéro de Châssis":"123", "Cylindrée":"49 cm³"}`

**Response (Standard)**:
```json
{
  "_reasoning_1": "Analysis confirming Identity Card CIN and Contract CIN match.",
  "_reasoning_2": "The expected values supplied are found successfully in the documents.",
  "documents_matched": true,
  "infos_list": [
    {
      "field_name": "Nom Prénom",
      "match_status": "matched"
    },
    {
      "field_name": "Cylindrée",
      "match_status": "not matched"
    }
  ]
}
```