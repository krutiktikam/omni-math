import asyncio
import logging
from pathlib import Path
from parsing_service import parsing_service
from vector_service import vector_service
from config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("omnimath.ingestion")

async def ingest_datasets():
    dataset_dir = Path(settings.storage_path) / "datasets"

    # Check for PDFs in the local dataset directory
    pdf_files = list(dataset_dir.glob("*.pdf"))

    if not pdf_files:
        logger.warning(f"No PDFs found in {dataset_dir}. Please place math PDFs there.")
        return

    for pdf_path in pdf_files:
        logger.info(f"Ingesting: {pdf_path.name}")
        chunks = parsing_service.extract_text_from_pdf(pdf_path)

        if chunks:
            await vector_service.add_documents(chunks)
            logger.info(f"Completed ingestion for {pdf_path.name}")

if __name__ == "__main__":
    asyncio.run(ingest_datasets())