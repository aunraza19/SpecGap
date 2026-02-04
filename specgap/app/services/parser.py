import pdfplumber
import io
import base64
import hashlib
from PIL import Image
import pandas as pd

# OCR imports
try:
    import pytesseract
    from pdf2image import convert_from_bytes
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False


def compute_file_hash(file_bytes: bytes) -> str:
    """
    Computes SHA-256 hash of file for duplicate detection and tracking.
    """
    return hashlib.sha256(file_bytes).hexdigest()


async def extract_text_with_ocr(file_bytes: bytes) -> str:
    """
    OCR fallback for scanned PDFs using Tesseract.
    Converts PDF pages to images and runs OCR on each.
    """
    if not OCR_AVAILABLE:
        return "Error: OCR libraries not installed. Install pytesseract and pdf2image."
    
    text_content = ""
    try:
        # Convert PDF pages to images (300 DPI for good OCR quality)
        images = convert_from_bytes(file_bytes, dpi=300)
        
        for i, img in enumerate(images):
            # Run Tesseract OCR on each page image
            page_text = pytesseract.image_to_string(img, lang='eng')
            if page_text.strip():
                text_content += f"--- Page {i + 1} (OCR) ---\n"
                text_content += page_text + "\n\n"
        
        return text_content if text_content.strip() else "Error: OCR could not extract any text."
        
    except Exception as e:
        return f"Error during OCR: {str(e)}"


async def extract_text_from_pdf(file_bytes: bytes, force_ocr: bool = False) -> str:
    """
    Extracts text AND TABLES from a PDF file stream.
    Optimized for preserving layout and structure for LLM understanding.
    
    Features:
    - Extracts Tables -> Converts to Markdown (Critical for structured data)
    - Extracts Text -> Adds Page Markers (Critical for Citations)
    - Fallback: Tesseract OCR for scanned documents
    """
    # Force OCR mode (useful for known scanned documents)
    if force_ocr:
        return await extract_text_with_ocr(file_bytes)
    
    text_content = ""
    try:
        # Wrap bytes in a stream so pdfplumber can read it
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            total_pages = len(pdf.pages)
            
            for i, page in enumerate(pdf.pages):
                page_num = i + 1
                page_content = f"\n--- PAGE {page_num} ---\n"
                
                # 1. Extract Tables first
                try:
                    tables = page.extract_tables()
                    if tables:
                        for table in tables:
                            # Filter out empty rows/tables
                            if not table or not any(row for row in table):
                                continue
                                
                            # Create DataFrame and convert to Markdown
                            # Assert first row is header if reasonable, else no header
                            df = pd.DataFrame(table[1:], columns=table[0]) if len(table) > 1 else pd.DataFrame(table)
                            markdown_table = df.to_markdown(index=False)
                            page_content += f"\n[Table on Page {page_num}]\n{markdown_table}\n\n"
                except Exception as e:
                    print(f"Table extraction warning: {e}")
                    pass 
                
                # 2. Extract Text
                # extract_text() maintains visual layout better than simple string dumps
                text = page.extract_text()
                if text:
                    page_content += text + "\n"
                
                text_content += page_content
        
        # OCR Fallback: If very little text extracted, it's likely a scanned PDF
        # Heuristic: Less than 50 chars per page on average = probably scanned
        avg_chars_per_page = len(text_content) / max(total_pages, 1)
        
        if not text_content.strip() or avg_chars_per_page < 50:
            if OCR_AVAILABLE:
                ocr_result = await extract_text_with_ocr(file_bytes)
                if "Error" not in ocr_result:
                    return ocr_result
                # If OCR also fails, return the original error
            return "Error: No text found. This appears to be a scanned PDF and OCR failed or is unavailable."
            
        return text_content
        
    except Exception as e:
        return f"Error parsing PDF: {str(e)}"

def encode_image_for_gemini(image_file: bytes, mime_type: str = "image/png"):
    """
    Prepares an image for Gemini Vision (Multimodal).
    Gemini expects a dictionary with 'mime_type' and 'data' (base64).
    """
    try:
        # 1. Validate it's a real image
        image = Image.open(io.BytesIO(image_file))
        
        # 2. Convert to Base64
        encoded_string = base64.b64encode(image_file).decode("utf-8")
        
        # 3. Return the specific format Google Generative AI expects
        return {
            "mime_type": mime_type,
            "data": encoded_string
        }
    except Exception as e:
        raise ValueError(f"Invalid image format: {str(e)}")