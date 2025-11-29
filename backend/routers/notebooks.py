from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from services.rag import rag_service


router = APIRouter(prefix="/api/notebooks", tags=["notebooks"])


class NotebookCreate(BaseModel):
    """Schema for creating a notebook."""
    notebook_id: str


class NotebookResponse(BaseModel):
    """Response schema for notebook operations."""
    message: str
    notebook_id: str
    exists: bool


@router.post("/", response_model=NotebookResponse)
def create_notebook(notebook_data: NotebookCreate):
    """
    Create a new notebook (Qdrant collection) for storing RAG data.
    
    This must be called before uploading files or inserting data into a notebook.
    """
    try:
        notebook_id = notebook_data.notebook_id
        
        if not notebook_id or not notebook_id.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="notebook_id cannot be empty"
            )
        
        # Check if notebook already exists
        if rag_service.client.collection_exists(notebook_id):
            return NotebookResponse(
                message=f"Notebook '{notebook_id}' already exists",
                notebook_id=notebook_id,
                exists=True
            )
        
        # Create the notebook
        rag_service.create_notebook(notebook_id)
        
        return NotebookResponse(
            message=f"Notebook '{notebook_id}' created successfully",
            notebook_id=notebook_id,
            exists=False
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating notebook: {str(e)}"
        )


@router.get("/{notebook_id}", response_model=NotebookResponse)
def get_notebook(notebook_id: str):
    """Check if a notebook exists."""
    exists = rag_service.client.collection_exists(notebook_id)
    
    return NotebookResponse(
        message=f"Notebook '{notebook_id}' {'exists' if exists else 'does not exist'}",
        notebook_id=notebook_id,
        exists=exists
    )


@router.delete("/{notebook_id}")
def delete_notebook(notebook_id: str):
    """Delete a notebook and all its data."""
    try:
        if not rag_service.client.collection_exists(notebook_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Notebook '{notebook_id}' not found"
            )
        
        rag_service.delete_notebook(notebook_id)
        
        return {
            "message": f"Notebook '{notebook_id}' deleted successfully",
            "notebook_id": notebook_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting notebook: {str(e)}"
        )



