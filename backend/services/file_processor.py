import os
import io
from typing import Optional, Tuple
from pathlib import Path

# PDF processing
try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None

# Image processing
try:
    from PIL import Image
    import pytesseract
except ImportError:
    Image = None
    pytesseract = None

# OpenAI Vision for advanced image processing
from services.transformers.image import image_recognition


class FileProcessor:
    """Service for processing PDFs and images to extract text."""
    
    SUPPORTED_PDF_EXTENSIONS = {'.pdf'}
    SUPPORTED_IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp'}
    
    def __init__(self, use_openai_vision: bool = True):
        """
        Initialize file processor.
        
        Args:
            use_openai_vision: If True, use OpenAI Vision API for image OCR instead of pytesseract
        """
        self.use_openai_vision = use_openai_vision
        
    def get_file_type(self, filename: str) -> Optional[str]:
        """Determine file type from extension."""
        ext = Path(filename).suffix.lower()
        if ext in self.SUPPORTED_PDF_EXTENSIONS:
            return 'pdf'
        elif ext in self.SUPPORTED_IMAGE_EXTENSIONS:
            return 'image'
        return None
    
    def process_pdf(self, file_content: bytes, filename: str) -> Tuple[str, dict]:
        """
        Extract text from PDF file.
        
        Args:
            file_content: PDF file content as bytes
            filename: Original filename
            
        Returns:
            Tuple of (extracted_text, metadata)
        """
        if PdfReader is None:
            raise ImportError("pypdf is not installed. Install it with: pip install pypdf")
        
        try:
            pdf_file = io.BytesIO(file_content)
            reader = PdfReader(pdf_file)
            
            text_parts = []
            metadata = {
                'type': 'pdf',
                'filename': filename,
                'num_pages': len(reader.pages),
                'pages_processed': []
            }
            
            for page_num, page in enumerate(reader.pages, 1):
                try:
                    page_text = page.extract_text()
                    if page_text.strip():
                        text_parts.append(f"--- Page {page_num} ---\n{page_text}")
                        metadata['pages_processed'].append(page_num)
                except Exception as e:
                    print(f"Error extracting text from page {page_num}: {e}")
                    continue
            
            full_text = "\n\n".join(text_parts)
            
            if not full_text.strip():
                raise ValueError("No text could be extracted from the PDF")
            
            return full_text, metadata
            
        except Exception as e:
            raise ValueError(f"Error processing PDF: {str(e)}")
    
    def process_image_with_ocr(self, file_content: bytes, filename: str) -> Tuple[str, dict]:
        """
        Extract text from image using pytesseract OCR.
        
        Args:
            file_content: Image file content as bytes
            filename: Original filename
            
        Returns:
            Tuple of (extracted_text, metadata)
        """
        if Image is None or pytesseract is None:
            raise ImportError(
                "PIL/Pillow and pytesseract are not installed. "
                "Install them with: pip install Pillow pytesseract"
            )
        
        try:
            image = Image.open(io.BytesIO(file_content))
            
            # Convert to RGB if necessary (some formats like PNG might have RGBA)
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Extract text using OCR
            text = pytesseract.image_to_string(image)
            
            metadata = {
                'type': 'image',
                'filename': filename,
                'processing_method': 'ocr_tesseract',
                'image_size': image.size,
                'image_format': image.format
            }
            
            if not text.strip():
                raise ValueError("No text could be extracted from the image using OCR")
            
            return text, metadata
            
        except Exception as e:
            raise ValueError(f"Error processing image with OCR: {str(e)}")
    
    def process_image_with_vision(self, file_content: bytes, filename: str) -> Tuple[str, dict]:
        """
        Extract text from image using OpenAI Vision API.
        
        Args:
            file_content: Image file content as bytes
            filename: Original filename
            
        Returns:
            Tuple of (extracted_text, metadata)
        """
        try:
            import base64
            
            # Encode image to base64
            base64_image = base64.b64encode(file_content).decode('utf-8')
            
            # Determine image format for data URL
            ext = Path(filename).suffix.lower()
            mime_type_map = {
                '.png': 'image/png',
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.gif': 'image/gif',
                '.webp': 'image/webp'
            }
            mime_type = mime_type_map.get(ext, 'image/png')
            
            # Call structured image recognition pipeline
            data_url = f"data:{mime_type};base64,{base64_image}"
            recognition_result = image_recognition([data_url])

            text_parts = recognition_result["chunks"][:]
            if recognition_result["description"]:
                text_parts.append(f"Description: {recognition_result['description']}")
            if recognition_result["summary"]:
                text_parts.append(f"Summary: {recognition_result['summary']}")

            text = "\n\n".join(part for part in text_parts if part.strip())

            metadata = {
                'type': 'image',
                'filename': filename,
                'processing_method': 'openai_vision_structured',
                'model': 'gpt-4o-mini',
                'tags': recognition_result.get('tags', []),
                'chunk_count': len(recognition_result.get('chunks', []))
            }
            
            if not text:
                raise ValueError("No text could be extracted from the image using Vision API")
            
            return text, metadata
            
        except Exception as e:
            raise ValueError(f"Error processing image with OpenAI Vision: {str(e)}")
    
    def process_image(self, file_content: bytes, filename: str) -> Tuple[str, dict]:
        """
        Extract text from image file.
        Uses OpenAI Vision if available, otherwise falls back to OCR.
        
        Args:
            file_content: Image file content as bytes
            filename: Original filename
            
        Returns:
            Tuple of (extracted_text, metadata)
        """
        if self.use_openai_vision:
            try:
                return self.process_image_with_vision(file_content, filename)
            except Exception as e:
                print(f"OpenAI Vision failed, falling back to OCR: {e}")
                # Fall back to OCR if Vision API fails
                return self.process_image_with_ocr(file_content, filename)
        else:
            return self.process_image_with_ocr(file_content, filename)
    
    def process_file(self, file_content: bytes, filename: str) -> Tuple[str, dict]:
        """
        Process a file (PDF or image) and extract text.
        
        Args:
            file_content: File content as bytes
            filename: Original filename
            
        Returns:
            Tuple of (extracted_text, metadata)
        """
        file_type = self.get_file_type(filename)
        
        if file_type == 'pdf':
            return self.process_pdf(file_content, filename)
        elif file_type == 'image':
            return self.process_image(file_content, filename)
        else:
            raise ValueError(
                f"Unsupported file type. Supported types: "
                f"PDF ({', '.join(self.SUPPORTED_PDF_EXTENSIONS)}), "
                f"Images ({', '.join(self.SUPPORTED_IMAGE_EXTENSIONS)})"
            )


# Global instance
file_processor = FileProcessor()
