import io
import os
import pytesseract
import pdfplumber
from PIL import Image
from PyPDF2 import PdfReader
from dotenv import load_dotenv

load_dotenv()

# Set Tesseract path from .env (critical on Windows)
tesseract_cmd = os.getenv("TESSERACT_CMD", "tesseract")
pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

DIGITAL_PDF_THRESHOLD = 100  # avg characters per page — below this → scanned


class PDFExtractor:

    def extract(self, file_bytes: bytes) -> str:
        if self._is_digital(file_bytes):
            return self._extract_digital(file_bytes)
        return self._extract_scanned(file_bytes)

    def validate_pdf(self, file_bytes: bytes) -> tuple[bool, str]:
        """Returns (is_valid, error_message)."""
        try:
            reader = PdfReader(io.BytesIO(file_bytes))
            if reader.is_encrypted:
                return False, "I was unable to read this document. Please ensure the file is not password-protected and try again."
            if len(reader.pages) == 0:
                return False, "The uploaded PDF appears to be empty. Please upload a valid document."
            return True, ""
        except Exception:
            return False, "I was unable to read this document. Please ensure the file is not password-protected and try again."

    def _is_digital(self, file_bytes: bytes) -> bool:
        try:
            with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                if not pdf.pages:
                    return False
                total_chars = sum(
                    len(page.extract_text() or "") for page in pdf.pages
                )
                avg_chars = total_chars / len(pdf.pages)
            return avg_chars >= DIGITAL_PDF_THRESHOLD
        except Exception:
            return False

    def _extract_digital(self, file_bytes: bytes) -> str:
        pages = []
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    pages.append(text.strip())
        return "\n\n".join(pages)

    def _extract_scanned(self, file_bytes: bytes) -> str:
        pages = []
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page in pdf.pages:
                # Render page as PIL image at 300 DPI for good OCR accuracy
                img = page.to_image(resolution=300).original
                text = pytesseract.image_to_string(img, lang="eng")
                if text.strip():
                    pages.append(text.strip())
        return "\n\n".join(pages)
