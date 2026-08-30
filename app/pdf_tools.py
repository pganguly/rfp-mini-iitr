from pypdf import PdfReader

def _extract_with_pypdf(pdf_bytes: bytes) -> str:
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


def extract_pdf_text(pdf_bytes: bytes) -> str:
    try:
        text = _extract_with_pypdf(pdf_bytes)
        return text
    except PDFExtractionError:
        return ""
