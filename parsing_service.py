import fitz  # PyMuPDF
import logging
from pathlib import Path
from typing import List, Dict, Any
import re

logger = logging.getLogger("omnimath.parsing")

class ParsingService:
    def __init__(self):
        pass

    def extract_text_from_pdf(self, pdf_path: Path) -> List[Dict[str, Any]]:
        """
        Extracts text and basic mathematical structures from a PDF.
        Returns a list of chunks with metadata.
        """
        chunks = []
        try:
            doc = fitz.open(str(pdf_path))
            for page_num, page in enumerate(doc):
                text = page.get_text("text")
                
                # Basic cleaning: remove multiple newlines
                clean_text = re.sub(r'\n+', '\n', text).strip()
                
                if clean_text:
                    chunks.append({
                        "content": clean_text,
                        "metadata": {
                            "source": pdf_path.name,
                            "page": page_num + 1,
                            "type": "text_chunk"
                        }
                    })
            doc.close()
            logger.info(f"Successfully parsed {pdf_path.name}: {len(chunks)} chunks found.")
            return chunks
        except Exception as e:
            logger.error(f"Failed to parse PDF {pdf_path}: {e}")
            return []

    def chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """
        Simple sliding window chunking for long text blocks.
        """
        chunks = []
        for i in range(0, len(text), chunk_size - overlap):
            chunks.append(text[i:i + chunk_size])
        return chunks

parsing_service = ParsingService()
