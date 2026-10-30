"""Text extraction service supporting PDF (PyMuPDF) and DOCX (python-docx)."""
import io
import re
import hashlib
from typing import Tuple
import fitz  # PyMuPDF
from docx import Document


class TextExtractionError(Exception):
    """Custom exception raised when file validation or extraction fails."""
    pass


class TextExtractor:
    PDF_MAGIC = b"%PDF"
    DOCX_MAGIC = b"PK\x03\x04"

    @classmethod
    def calculate_hash(cls, file_bytes: bytes) -> str:
        """Calculate SHA-256 hash of file content for deduplication."""
        return hashlib.sha256(file_bytes).hexdigest()

    @classmethod
    def validate_file(cls, filename: str, file_bytes: bytes, max_size_mb: int = 10) -> str:
        """Validate filename extension, size, and file signature."""
        if not file_bytes or len(file_bytes) == 0:
            raise TextExtractionError("The uploaded file is empty.")

        size_mb = len(file_bytes) / (1024 * 1024)
        if size_mb > max_size_mb:
            raise TextExtractionError(
                f"File size ({size_mb:.2f} MB) exceeds maximum allowed limit of {max_size_mb} MB."
            )

        lower_name = filename.lower()
        if lower_name.endswith(".pdf"):
            if not file_bytes.startswith(cls.PDF_MAGIC):
                raise TextExtractionError("Invalid PDF file: Missing standard %PDF signature.")
            return "pdf"
        elif lower_name.endswith(".docx"):
            if not file_bytes.startswith(cls.DOCX_MAGIC):
                raise TextExtractionError("Invalid DOCX file: Missing standard ZIP/DOCX signature.")
            return "docx"
        else:
            raise TextExtractionError("Unsupported file type. Only PDF (.pdf) and Word (.docx) files are supported.")

    @classmethod
    def extract_from_pdf(cls, file_bytes: bytes) -> Tuple[str, bool, int]:
        """Extract text from PDF using PyMuPDF (fitz) and detect scanned pages."""
        try:
            doc = fitz.open(stream=file_bytes, filetype="pdf")
        except Exception as e:
            raise TextExtractionError(f"Corrupted or unreadable PDF file: {str(e)}")

        page_count = len(doc)
        if page_count == 0:
            raise TextExtractionError("PDF file contains no pages.")

        page_texts = []
        total_chars = 0

        for page_idx in range(page_count):
            page = doc.load_page(page_idx)
            text = page.get_text("text", sort=True) or ""
            page_texts.append(text)
            total_chars += len(text.strip())

        full_text = "\n\n".join(page_texts)
        is_scanned = False

        # If very few characters extracted across pages, detect image-only / scanned PDF
        if total_chars < 50:
            is_scanned = True
            # Attempt OCR fallback if pytesseract is available
            try:
                import pytesseract
                from PIL import Image

                ocr_texts = []
                for page_idx in range(page_count):
                    page = doc.load_page(page_idx)
                    pix = page.get_pixmap()
                    img = Image.open(io.BytesIO(pix.tobytes("png")))
                    ocr_text = pytesseract.image_to_string(img)
                    if ocr_text:
                        ocr_texts.append(ocr_text)
                if ocr_texts:
                    full_text = "\n\n".join(ocr_texts)
            except Exception:
                # OCR dependency not configured or failed; keep is_scanned flag
                pass

        if not full_text.strip() and not is_scanned:
            raise TextExtractionError("No readable text found in the PDF document.")

        return cls.normalize_text(full_text), is_scanned, page_count

    @classmethod
    def extract_from_docx(cls, file_bytes: bytes) -> Tuple[str, bool, int]:
        """Extract text from DOCX including both paragraphs and tables."""
        try:
            docx_file = io.BytesIO(file_bytes)
            doc = Document(docx_file)
        except Exception as e:
            raise TextExtractionError(f"Corrupted or unreadable DOCX file: {str(e)}")

        extracted_lines = []

        # Extract paragraphs
        for para in doc.paragraphs:
            text = para.text.strip()
            if text:
                extracted_lines.append(text)

        # Extract tables with boundary separation
        for table in doc.tables:
            extracted_lines.append("")  # Blank line before table
            for row in table.rows:
                row_cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                # Deduplicate identical adjacent cells from merged cells
                cleaned_cells = []
                for c in row_cells:
                    if not cleaned_cells or cleaned_cells[-1] != c:
                        cleaned_cells.append(c)
                if cleaned_cells:
                    extracted_lines.append(" | ".join(cleaned_cells))
            extracted_lines.append("")  # Blank line after table

        full_text = "\n".join(extracted_lines)
        if not full_text.strip():
            raise TextExtractionError("No readable text found in the DOCX document.")

        return cls.normalize_text(full_text), False, 1

    @classmethod
    def normalize_text(cls, text: str) -> str:
        """Normalize line endings, whitespace, and special unicode bullet points."""
        if not text:
            return ""

        # Normalize special unicode bullets & symbols
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        text = text.replace("\u2022", "•").replace("\u2023", "•").replace("\u25e6", "•").replace("\u2043", "•")
        text = text.replace("\u00a0", " ")  # Non-breaking space
        text = text.replace("\u2013", "-").replace("\u2014", "-")  # En-dash and Em-dash
        text = re.sub(r"[\u200b\u200c\u200d\ufeff\u200e\u200f]", "", text)  # Zero-width chars

        # Collapse trailing horizontal whitespace per line
        lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.split("\n")]

        # Avoid excessive blank lines (max 2 consecutive newlines)
        cleaned_lines = []
        blank_count = 0
        for line in lines:
            if not line:
                blank_count += 1
                if blank_count <= 2:
                    cleaned_lines.append("")
            else:
                blank_count = 0
                cleaned_lines.append(line)

        return "\n".join(cleaned_lines).strip()

    @classmethod
    def extract_text(cls, filename: str, file_bytes: bytes, max_size_mb: int = 10):
        """Unified entry point for extraction."""
        file_type = cls.validate_file(filename, file_bytes, max_size_mb)
        file_hash = cls.calculate_hash(file_bytes)

        if file_type == "pdf":
            raw_text, is_scanned, page_count = cls.extract_from_pdf(file_bytes)
        else:
            raw_text, is_scanned, page_count = cls.extract_from_docx(file_bytes)

        return {
            "text": raw_text,
            "is_scanned": is_scanned,
            "page_count": page_count,
            "file_hash": file_hash,
            "file_size": len(file_bytes),
        }
