from fastapi import APIRouter, UploadFile, File, HTTPException, status, Form, Depends
from sqlalchemy.orm import Session
from typing import Optional
from database import get_db
from services.file_processor import file_processor
from services.rag import rag_service
from pydantic import BaseModel, Field


router = APIRouter(prefix="/api/files", tags=["files"])


class FileUploadResponse(BaseModel):
    """Response schema for file upload."""
    message: str
    notebook_id: str
    filename: str
    file_type: str
    text_length: int
    metadata: dict
    status: str = Field(default="success")


@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    notebook_id: str = Form(..., description="Notebook ID where the file will be stored"),
    file: UploadFile = File(..., description="PDF or image file to upload"),
    source: Optional[str] = Form(None, description="Optional source identifier for the file"),
    db: Session = Depends(get_db)
):
    """
    Upload and process a PDF or image file.
    
    The file will be processed to extract text, which will then be added to the specified notebook
    in the RAG system for vector search.
    
    Supported formats:
    - PDF: .pdf
    - Images: .png, .jpg, .jpeg, .gif, .bmp, .tiff, .webp
    """
    try:
        # Validate file type
        file_type = file_processor.get_file_type(file.filename)
        if file_type is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type. Supported: PDF and common image formats."
            )
        
        # Read file content
        file_content = await file.read()
        
        if len(file_content) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File is empty"
            )
        
        # Check notebook exists
        if not rag_service.client.collection_exists(notebook_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Notebook '{notebook_id}' not found. Create it first using the notebook creation endpoint."
            )
        
        # Process file to extract text
        extracted_text, metadata = file_processor.process_file(file_content, file.filename)
        
        # Insert extracted text into RAG system
        source_name = source or file.filename
        rag_service.insert_data(
            notebook_id=notebook_id,
            data=extracted_text,
            source=source_name
        )
        
        return FileUploadResponse(
            message=f"File '{file.filename}' processed and added to notebook '{notebook_id}'",
            notebook_id=notebook_id,
            filename=file.filename,
            file_type=metadata.get('type', 'unknown'),
            text_length=len(extracted_text),
            metadata=metadata,
            status="success"
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing file: {str(e)}"
        )


@router.post("/upload-multiple")
async def upload_multiple_files(
    notebook_id: str = Form(..., description="Notebook ID where files will be stored"),
    files: list[UploadFile] = File(..., description="List of PDF or image files to upload"),
    source: Optional[str] = Form(None, description="Optional source identifier for all files"),
    db: Session = Depends(get_db)
):
    """
    Upload and process multiple PDF or image files at once.
    
    Returns a list of results for each file processed.
    """
    results = []
    
    # Check notebook exists
    if not rag_service.client.collection_exists(notebook_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Notebook '{notebook_id}' not found. Create it first."
        )
    
    for file in files:
        try:
            # Validate file type
            file_type = file_processor.get_file_type(file.filename)
            if file_type is None:
                results.append({
                    "filename": file.filename,
                    "status": "error",
                    "error": "Unsupported file type"
                })
                continue
            
            # Read file content
            file_content = await file.read()
            
            if len(file_content) == 0:
                results.append({
                    "filename": file.filename,
                    "status": "error",
                    "error": "File is empty"
                })
                continue
            
            # Process file
            extracted_text, metadata = file_processor.process_file(file_content, file.filename)
            
            # Insert into RAG
            source_name = source or file.filename
            rag_service.insert_data(
                notebook_id=notebook_id,
                data=extracted_text,
                source=source_name
            )
            
            results.append({
                "filename": file.filename,
                "status": "success",
                "file_type": metadata.get('type', 'unknown'),
                "text_length": len(extracted_text),
                "metadata": metadata
            })
            
        except Exception as e:
            results.append({
                "filename": file.filename,
                "status": "error",
                "error": str(e)
            })
    
    return {
        "notebook_id": notebook_id,
        "total_files": len(files),
        "successful": sum(1 for r in results if r.get("status") == "success"),
        "failed": sum(1 for r in results if r.get("status") == "error"),
        "results": results
    }
