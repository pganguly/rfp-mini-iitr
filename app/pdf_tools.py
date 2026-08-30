from __future__ import annotations

from io import BytesIO
from typing import Literal

PDFBackend = Literal["auto", "pymupdf", "pypdf"]


class PDFExtractionError(RuntimeError):
    """Raised when PDF text extraction fails."""


def _extract_with_pymupdf(pdf_bytes: bytes) -> str:
    """Extract page-delimited text using the PyMuPDF package."""
    try:
        import pymupdf
    except ImportError as exc:
        raise PDFExtractionError(
            "PyMuPDF is not installed. Run: pip install PyMuPDF"
        ) from exc

    try:
        doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
        pages: list[str] = []

        for page_number, page in enumerate(doc, start=1):
            text = page.get_text("text") or ""
            pages.append(f"[PAGE {page_number}]\n{text.strip()}")

        doc.close()
        return "\n\n".join(pages).strip()

    except Exception as exc:
        raise PDFExtractionError(
            f"PyMuPDF extraction failed: {exc}"
        ) from exc


def _extract_with_pypdf(pdf_bytes: bytes) -> str:
    """Extract page-delimited text using pypdf."""
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise PDFExtractionError(
            "pypdf is not installed. Run: pip install pypdf"
        ) from exc

    try:
        reader = PdfReader(BytesIO(pdf_bytes))

        if reader.is_encrypted:
            try:
                decrypt_result = reader.decrypt("")
                if decrypt_result == 0:
                    raise PDFExtractionError(
                        "The PDF is password-protected and could not be decrypted."
                    )
            except PDFExtractionError:
                raise
            except Exception as exc:
                raise PDFExtractionError(
                    "The PDF is password-protected and could not be decrypted."
                ) from exc

        pages: list[str] = []
        for page_number, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            pages.append(f"[PAGE {page_number}]\n{text.strip()}")

        return "\n\n".join(pages).strip()

    except PDFExtractionError:
        raise
    except Exception as exc:
        raise PDFExtractionError(
            f"pypdf extraction failed: {exc}"
        ) from exc


def extract_pdf_text(
    pdf_bytes: bytes,
    backend: PDFBackend = "auto",
) -> str:
    """
    Extract text from a PDF.

    backend:
      "pymupdf" -> use PyMuPDF only
      "pypdf"   -> use pypdf only
      "auto"    -> try PyMuPDF first, then pypdf

    The returned text preserves page boundaries using [PAGE N] markers.
    """
    if not pdf_bytes:
        raise PDFExtractionError("The uploaded PDF is empty.")

    backend = (backend or "auto").lower()

    if backend == "pymupdf":
        text = _extract_with_pymupdf(pdf_bytes)
        if not text.strip():
            raise PDFExtractionError(
                "PyMuPDF completed but no extractable text was found."
            )
        return text

    if backend == "pypdf":
        text = _extract_with_pypdf(pdf_bytes)
        if not text.strip():
            raise PDFExtractionError(
                "pypdf completed but no extractable text was found."
            )
        return text

    if backend != "auto":
        raise ValueError(
            f"Unsupported PDF backend '{backend}'. "
            "Choose 'auto', 'pymupdf', or 'pypdf'."
        )

    errors: list[str] = []

    # Preferred extractor
    try:
        text = _extract_with_pymupdf(pdf_bytes)
        if text.strip():
            return text
        errors.append("PyMuPDF returned no extractable text.")
    except Exception as exc:
        errors.append(str(exc))

    # Fallback extractor
    try:
        text = _extract_with_pypdf(pdf_bytes)
        if text.strip():
            return text
        errors.append("pypdf returned no extractable text.")
    except Exception as exc:
        errors.append(str(exc))

    raise PDFExtractionError(
        "Unable to extract text using either PyMuPDF or pypdf. "
        + " | ".join(errors)
    )
