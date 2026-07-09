import os
import shutil
from fastapi import APIRouter, UploadFile, File, HTTPException, status
from app.services.parser import PDFParserService
from app.services.vector_db import VectorDBService
from app.core.config import settings

router = APIRouter()
parser_service = PDFParserService()
vector_db_service = VectorDBService(collection_name=settings.COLLECTION_NAME)

@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_document(file: UploadFile = File(...)):
    """
    Receives an uploaded PDF file, extracts and chunks text, 
    and indexes the resulting vectors in Qdrant.
    """
    # 1. Validate file extension
    if not file.filename.endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Only PDF documents are supported."
        )
        
    # Ensure temporary upload directory exists
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    temp_file_path = os.path.join(settings.UPLOAD_DIR, file.filename)
    
    # 2. Save the uploaded file stream to local disk temporarily
    try:
        with open(temp_file_path, "wb") as buffer:
            # Copy file content in chunks to avoid memory consumption spikes
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file on disk: {e}"
        )
        
    # 3. Parse and chunk the PDF
    try:
        # Extract pages and page numbers
        pages = parser_service.parse_pdf(temp_file_path)
        
        if not pages:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="The PDF contains no extractable text."
            )
            
        # Chunk text recursively
        chunks, metadata = parser_service.chunk_text(
            pages=pages,
            doc_name=file.filename,
            chunk_size=600,
            chunk_overlap=120
        )
        
        # 4. Ingest vectors into Qdrant
        success = vector_db_service.upsert_documents(chunks, metadata)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to index document chunks into vector database."
            )
            
        return {
            "status": "success",
            "filename": file.filename,
            "pages_extracted": len(pages),
            "chunks_created": len(chunks)
        }
        
    finally:
        # 5. Guaranteed cleanup of the temporary file to prevent disk bloat
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
