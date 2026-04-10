import os
import shutil
import uuid
import logging
import time
import json
from typing import List

import uvicorn
from fastapi import APIRouter, FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

from verifier import verify_documents

app = FastAPI(
    title="Deux Roues Verification API",
    description="API for verifying Tunisian vehicle transaction documents using Gemini"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# API router
api_v1 = APIRouter(prefix="/api/v1/deux-roues", tags=["deux-roues"])

UPLOAD_DIR = "temp_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@api_v1.post("/verify")
async def verify_endpoint(
    files: List[UploadFile] = File(...),
    expected_values: str = Form(None, description="Optional JSON string of the expected values to verify against"),
    additional_text: str = Form(None, description="Any extra text instructions or context")
):
    """
    Endpoint to upload images (CIN, Contract, Receipt) and run the Gemini Document Verification against optional expected values and extra text context.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded.")
        
    parsed_expected = None
    if expected_values:
        try:
            parsed_expected = json.loads(expected_values)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="expected_values must be a valid JSON string.")
            
    request_id = str(uuid.uuid4())
    temp_paths = []

    try:
        start_total = time.time()
        logger.info(f"[{request_id}] Receiving {len(files)} files...")

        # Securely save uploaded files to a temporary folder
        for file in files:
            temp_path = os.path.join(UPLOAD_DIR, f"{request_id}_{file.filename}")
            with open(temp_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            temp_paths.append(temp_path)

        logger.info(f"[{request_id}] Starting Gemini Verification for {len(temp_paths)} images...")
        t_verif = time.time()
        
        # Pass the paths directly to your existing verifier function
        result_text = verify_documents(
            temp_paths, 
            expected_values=parsed_expected,
            additional_text=additional_text
        )
        
        logger.info(f"[{request_id}] Complete! Took {time.time() - t_verif:.2f}s")
        
        # We try to parse it into JSON as requested by the prompt
        try:
            return json.loads(result_text)
        except json.JSONDecodeError:
            # Fallback if Gemini somehow didn't return pure JSON
            return {"raw_result": result_text}

    except Exception as e:
        logger.error(f"[{request_id}] Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur lors du traitement: {str(e)}")

    finally:
        # Always clean up the server's storage after sending response
        for p in temp_paths:
            if os.path.exists(p):
                os.remove(p)
        logger.info(f"[{request_id}] Temporary files cleaned up.")


@api_v1.get("/health")
def health_check():
    return {"status": "ok", "service": "Deux Roues Verification API"}


app.include_router(api_v1)

@app.get("/")
def root_redirect():
    return {
        "status": "running",
        "message": "Deux Roues API is active. POST documents to /api/v1/deux-roues/verify",
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8081)