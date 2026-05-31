import io
import pdfplumber
from PIL import Image
import pytesseract
from PyPDF2 import PdfReader

DIGITAL_PDF_THRESHOLD = 100  # characters per page


class PDFExtractor:
    def extract(self, file_bytes: bytes) -> str:
        if self._is_digital(file_bytes):
            return self._extract_digital(file_bytes)
        return self._extract_scanned(file_bytes)

    def _is_digital(self, file_bytes: bytes) -> bool:
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            total_chars = sum(
                len(page.extract_text() or "") for page in pdf.pages
            )
            avg_chars_per_page = total_chars / max(len(pdf.pages), 1)
        return avg_chars_per_page >= DIGITAL_PDF_THRESHOLD

    def _extract_digital(self, file_bytes: bytes) -> str:
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            pages = [page.extract_text() or "" for page in pdf.pages]
        return "\n\n".join(pages)

    def _extract_scanned(self, file_bytes: bytes) -> str:
        """OCR fallback for scanned/image PDFs. Implemented in Phase 3."""
        raise NotImplementedError("Tesseract OCR fallback implemented in Phase 3")

    def validate_pdf(self, file_bytes: bytes) -> bool:
        try:
            reader = PdfReader(io.BytesIO(file_bytes))
            return len(reader.pages) > 0 and not reader.is_encrypted
        except Exception:
            return False
