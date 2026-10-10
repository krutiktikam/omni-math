import asyncio
import logging
from pathlib import Path
from parsing_service import parsing_service
from vector_service import vector_service
from config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("omnimath.ingestion.programming")

async def ingest_programming_docs():
    docs_dir = Path(settings.storage_path) / "programming_docs"

    # Check for markdown files in the programming_docs directory
    md_files = list(docs_dir.glob("*.md"))

    if not md_files:
        logger.warning(f"No markdown files found in {docs_dir}. Please place programming documentation there.")
        return

    for md_path in md_files:
        logger.info(f"Ingesting: {md_path.name}")
        try:
            # Read the markdown file
            content = md_path.read_text(encoding="utf-8")

            # Parse it using our enhanced parsing service
            chunks = parsing_service.parse_file(md_path)

            if chunks:
                # Add documents to vector database
                await vector_service.add_documents(chunks)
                logger.info(f"Completed ingestion for {md_path.name} ({len(chunks)} chunks)")
            else:
                logger.warning(f"No chunks generated from {md_path.name}")

        except Exception as e:
            logger.error(f"Failed to ingest {md_path.name}: {e}")

if __name__ == "__main__":
    asyncio.run(ingest_programming_docs())