"""
Document Handler
Handles text document processing (PDF, DOCX, TXT) with comprehensive logging
"""

import PyPDF2
from docx import Document
from utils.logger import get_logger

logger = get_logger(__name__)


def extract_from_pdf(file_path: str) -> str:
    """
    Extract text from PDF file

    Args:
        file_path (str): Path to PDF file

    Returns:
        str: Extracted text content

    Raises:
        Exception: If extraction fails
    """
    logger.info(f"Extracting text from PDF: {file_path}")
    logger.debug(f"File path: {file_path}")

    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            page_count = len(pdf_reader.pages)

            logger.debug(f"PDF has {page_count} pages")

            text = ""
            for i, page in enumerate(pdf_reader.pages):
                logger.debug(f"Extracting page {i+1}/{page_count}")
                page_text = page.extract_text()
                text += page_text + "\n"
                logger.debug(f"  Page {i+1}: {len(page_text)} characters")

            text = text.strip()

            logger.info(f"✓ PDF extraction successful")
            logger.info(f"  Total pages: {page_count}")
            logger.info(f"  Total characters: {len(text)}")
            logger.debug(f"  Text preview: {text[:200]}...")

            return text

    except Exception as e:
        logger.error(f"❌ Failed to extract from PDF: {file_path}")
        logger.error(f"Error: {str(e)}")
        logger.exception("Full error traceback:")
        raise Exception(f"Error reading PDF: {str(e)}")


def extract_from_docx(file_path: str) -> str:
    """
    Extract text from DOCX file

    Args:
        file_path (str): Path to DOCX file

    Returns:
        str: Extracted text content

    Raises:
        Exception: If extraction fails
    """
    logger.info(f"Extracting text from DOCX: {file_path}")
    logger.debug(f"File path: {file_path}")

    try:
        doc = Document(file_path)
        paragraph_count = len(doc.paragraphs)

        logger.debug(f"DOCX has {paragraph_count} paragraphs")

        text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
        text = text.strip()

        logger.info(f"✓ DOCX extraction successful")
        logger.info(f"  Total paragraphs: {paragraph_count}")
        logger.info(f"  Total characters: {len(text)}")
        logger.debug(f"  Text preview: {text[:200]}...")

        return text

    except Exception as e:
        logger.error(f"❌ Failed to extract from DOCX: {file_path}")
        logger.error(f"Error: {str(e)}")
        logger.exception("Full error traceback:")
        raise Exception(f"Error reading DOCX: {str(e)}")


def extract_from_txt(file_path: str) -> str:
    """
    Extract text from TXT file

    Args:
        file_path (str): Path to TXT file

    Returns:
        str: Extracted text content

    Raises:
        Exception: If extraction fails
    """
    logger.info(f"Extracting text from TXT: {file_path}")
    logger.debug(f"File path: {file_path}")

    try:
        logger.debug("Attempting UTF-8 encoding...")
        with open(file_path, 'r', encoding='utf-8') as file:
            text = file.read().strip()

        logger.info(f"✓ TXT extraction successful (UTF-8)")
        logger.info(f"  Total characters: {len(text)}")
        logger.debug(f"  Text preview: {text[:200]}...")

        return text

    except UnicodeDecodeError:
        logger.warning("UTF-8 decoding failed, trying latin-1...")

        try:
            with open(file_path, 'r', encoding='latin-1') as file:
                text = file.read().strip()

            logger.info(f"✓ TXT extraction successful (latin-1)")
            logger.info(f"  Total characters: {len(text)}")
            logger.debug(f"  Text preview: {text[:200]}...")

            return text

        except Exception as e:
            logger.error(f"❌ Failed to extract from TXT with latin-1: {file_path}")
            logger.error(f"Error: {str(e)}")
            logger.exception("Full error traceback:")
            raise Exception(f"Error reading TXT: {str(e)}")

    except Exception as e:
        logger.error(f"❌ Failed to extract from TXT: {file_path}")
        logger.error(f"Error: {str(e)}")
        logger.exception("Full error traceback:")
        raise Exception(f"Error reading TXT: {str(e)}")


def process_document(file_path: str, file_extension: str) -> str:
    """
    Process document based on file extension

    Args:
        file_path (str): Path to document file
        file_extension (str): File extension (pdf, docx, txt)

    Returns:
        str: Extracted text content

    Raises:
        Exception: If processing fails or format unsupported
    """
    ext = file_extension.lower()

    logger.info("="*60)
    logger.info(f"PROCESSING DOCUMENT: {ext.upper()}")
    logger.info("="*60)

    logger.debug(f"File: {file_path}")
    logger.debug(f"Extension: {ext}")

    if ext == 'pdf':
        return extract_from_pdf(file_path)
    elif ext == 'docx':
        return extract_from_docx(file_path)
    elif ext == 'txt':
        return extract_from_txt(file_path)
    else:
        logger.error(f"❌ Unsupported document format: {ext}")
        raise Exception(f"Unsupported document format: {ext}")
