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
    CIN_doc: UploadFile = File(..., description="Document CIN (Image)"),
    Contract_doc: UploadFile = File(..., description="Document Contrat (Image)"),
    Other_docs: List[UploadFile] = File(default=[], description="Autres documents (Optionnels)"),
    Full_Name: str = Form(None, description="Nom et prénom"),
    CIN_number: str = Form(None, description="Numéro de CIN"),
    Cylender_number: str = Form(None, description="Cylindrée"),
    Imm_number: str = Form(None, description="Numéro d'immatriculation"),
    additional_text: str = Form(None, description="Any extra text instructions or context")
):
    """
    Endpoint to upload images and run the Gemini Document Verification against text field values.
    """
    # Build expected_values dictionary dynamically from text inputs
    parsed_expected = {}
    if Full_Name: parsed_expected["Full_Name"] = Full_Name
    if CIN_number: parsed_expected["CIN_number"] = CIN_number
    if Cylender_number: parsed_expected["Cylender_number"] = Cylender_number
    if Imm_number: parsed_expected["Imm_number"] = Imm_number
    
    if not parsed_expected:
        parsed_expected = None
            
    request_id = str(uuid.uuid4())
    temp_paths = []
    doc_names = []
    
    # Consolidate all files into a single list while tracking their distinct type names
    all_files = []
    
    if CIN_doc:
        all_files.append(CIN_doc)
        doc_names.append("CIN_doc")
        
    if Contract_doc:
        all_files.append(Contract_doc)
        doc_names.append("Contract_doc")
        
    if Other_docs:
        for idx, doc in enumerate(Other_docs):
            if doc.filename:
                all_files.append(doc)
                doc_names.append(f"Other_doc_{idx}")

    try:
        start_total = time.time()
        logger.info(f"[{request_id}] Receiving {len(all_files)} files...")

        # Securely save uploaded files to a temporary folder
        for idx, file in enumerate(all_files):
            temp_path = os.path.join(UPLOAD_DIR, f"{request_id}_{idx}_{file.filename}")
            with open(temp_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            temp_paths.append(temp_path)

        logger.info(f"[{request_id}] Starting Gemini Verification for {len(temp_paths)} images...")
        t_verif = time.time()
        
        # Pass the paths directly to your existing verifier function alongside their specific labels
        result_text = verify_documents(
            temp_paths, 
            expected_values=parsed_expected,
            additional_text=additional_text,
            doc_names=doc_names
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