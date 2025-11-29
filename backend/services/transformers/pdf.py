import os
from PIL import Image
from pdf2image import convert_from_path
from surya.foundation import FoundationPredictor
from surya.recognition import RecognitionPredictor
from surya.detection import DetectionPredictor
from langchain_text_splitters import RecursiveCharacterTextSplitter


class UniversalOCR:
    def __init__(self, langs=["uk", "en"]):
        self.langs = langs
        print("🚀 Initializing Surya OCR predictors...")
        
        # Initialize predictors using the new API
        self.foundation_predictor = FoundationPredictor()
        self.recognition_predictor = RecognitionPredictor(self.foundation_predictor)
        self.detection_predictor = DetectionPredictor()
        
        print("✅ OCR predictors initialized")

    def process_image(self, image_path_or_obj):
        # Open image
        if isinstance(image_path_or_obj, str):
            image = Image.open(image_path_or_obj).convert("RGB")
        else:
            image = image_path_or_obj.convert("RGB")

        # Run OCR using the new API
        # predictions is a list, one per image
        predictions = self.recognition_predictor(
            [image], 
            det_predictor=self.detection_predictor
        )

        # Extract text from predictions
        result_text = []
        if predictions and len(predictions) > 0:
            prediction = predictions[0]
            
            # Handle different prediction structures
            # Try to get text_lines attribute or key
            text_lines = None
            if hasattr(prediction, 'text_lines'):
                text_lines = prediction.text_lines
            elif isinstance(prediction, dict) and 'text_lines' in prediction:
                text_lines = prediction['text_lines']
            elif hasattr(prediction, 'lines'):
                text_lines = prediction.lines
            
            # Extract text from lines
            if text_lines:
                for line in text_lines:
                    text = None
                    if isinstance(line, dict):
                        text = line.get('text') or line.get('text_line')
                    elif hasattr(line, 'text'):
                        text = line.text
                    elif isinstance(line, str):
                        text = line
                    
                    if text:
                        result_text.append(text)

        return "\n".join(result_text)


# Initialize OCR engine as a module-level singleton
_ocr_engine = None


def _get_ocr_engine():
    """Get or create the OCR engine singleton."""
    global _ocr_engine
    if _ocr_engine is None:
        _ocr_engine = UniversalOCR()
    return _ocr_engine


def process_pdf(pdf_path: str, chunk_size: int = 500, chunk_overlap: int = 50) -> list[str]:
    """
    Process a PDF file by converting it to images, running OCR on each page,
    and returning the text split into chunks.

    Args:
        pdf_path: Path to the PDF file
        chunk_size: Maximum size of each text chunk
        chunk_overlap: Number of characters to overlap between chunks

    Returns:
        List of text chunks extracted from the PDF
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    print(f"📄 Processing PDF: {pdf_path}")

    # Convert PDF pages to images
    try:
        print("🖼️  Converting PDF pages to images...")
        images = convert_from_path(pdf_path, dpi=300)
        print(f"✅ Converted {len(images)} pages to images")
    except Exception as e:
        raise RuntimeError(f"Failed to convert PDF to images: {str(e)}")

    # Initialize OCR engine
    ocr_engine = _get_ocr_engine()

    # Process each page with OCR
    all_text_parts = []
    for i, image in enumerate(images, 1):
        print(f"🔍 Processing page {i}/{len(images)} with OCR...")
        try:
            page_text = ocr_engine.process_image(image)
            if page_text.strip():
                all_text_parts.append(page_text)
                print(f"✅ Page {i} processed: {len(page_text)} characters extracted")
            else:
                print(f"⚠️  Page {i} returned no text")
        except Exception as e:
            print(f"❌ Error processing page {i}: {str(e)}")
            continue

    # Combine all text from all pages
    combined_text = "\n\n".join(all_text_parts)

    if not combined_text.strip():
        print("⚠️  No text extracted from PDF")
        return []

    print(f"📝 Total text extracted: {len(combined_text)} characters")

    # Split into chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        is_separator_regex=False,
    )

    chunks = text_splitter.split_text(combined_text)
    print(f"✂️  Split into {len(chunks)} chunks")

    return chunks


# --- Приклад використання ---
if __name__ == "__main__":
    # Example usage
    import sys
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
        chunks = process_pdf(pdf_path)
        print("\n--- Chunks ---\n")
        for i, chunk in enumerate(chunks, 1):
            print(f"\n--- Chunk {i} ---\n{chunk}\n")
    else:
        print("Usage: python pdf.py <path_to_pdf>")