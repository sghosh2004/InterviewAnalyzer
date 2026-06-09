import logging
from io import BytesIO
from pypdf import PdfReader

logger = logging.getLogger(__name__)

def extract_text_from_pdf(file) -> str:
    try:
        file.seek(0)
        pdf_bytes = file.read()

        logger.info("PDF Size: %s bytes", len(pdf_bytes))

        reader = PdfReader(BytesIO(pdf_bytes))

        extracted_pages = []

        logger.info("Total Pages: %s", len(reader.pages))

        for page_num, page in enumerate(reader.pages):
            try:
                text = page.extract_text()

                logger.info(
                    "Page %s Text Length: %s",
                    page_num + 1,
                    len(text) if text else 0
                )

                if text and text.strip():
                    extracted_pages.append(text.strip())

            except Exception as page_error:
                logger.warning(
                    "PDF page %s extraction error: %s",
                    page_num + 1,
                    page_error
                )

        extracted_text = "\n\n".join(extracted_pages).strip()

        logger.info(
            "Total Extracted Characters: %s",
            len(extracted_text)
        )

        return extracted_text

    except Exception as exc:
        raise RuntimeError(
            f"Failed to extract PDF text: {exc}"
        ) from exc


def build_document_record(file_name: str, extracted_text: str) -> dict:
    return {
        "file_name": file_name,
        "extracted_text": extracted_text,
    }