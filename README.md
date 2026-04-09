# Deux Roues Validation API

A precise and structured API service utilizing Google's Gemini LLM architecture to automatically cross-verify Tunisian vehicle transaction documents, specifically targeting Identity Cards (CIN), Sales Contracts/Invoices, and Receipts (Quittances).

## Features
- **Multi-Document Verification**: Compares logic between Identity, Contracts, and Receipts natively.
- **Strict JSON Structuring**: Forges Gemini output into an exact schema via targeted prompting (`response_mime_type="application/json"`).
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
Accepts `multipart/form-data` with images matching the internal key `files`.

**Input**: At least 2-3 image documents (.jpg, .png).
**Response (Standard)**:
```json
{
  "verification_results": [
    {
      "field_name": "Nom Prénom",
      "values_in_documents": {
        "document_1": "John Doe",
        "document_2": "John Doe",
        "document_3": "John Doe"
      },
      "match_status": "matched"
    }
  ]
}
```