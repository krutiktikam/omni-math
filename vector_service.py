import chromadb
from chromadb.config import Settings as ChromaSettings
from chromadb.utils import embedding_functions
import logging
from pathlib import Path
from typing import List, Dict, Any
from config import settings

logger = logging.getLogger("omnimath.vector")

class VectorService:
    def __init__(self, db_path: Path = Path(settings.storage_path) / "vector_db"):
        self.db_path = db_path
        self.db_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize persistent client
        self.client = chromadb.PersistentClient(path=str(self.db_path))
        
        # Default embedding function: lightweight bge-small (using SentenceTransformer locally)
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2" # Fast, low resource
        )
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name="math_knowledge",
            embedding_function=self.embedding_fn
        )

    async def add_documents(self, chunks: List[Dict[str, Any]], batch_size: int = 250):
        """
        Adds parsed chunks to the vector database in safe batches.
        """
        import re
        total = len(chunks)
        if total == 0:
            return

        for start_idx in range(0, total, batch_size):
            end_idx = min(start_idx + batch_size, total)
            batch = chunks[start_idx:end_idx]
            
            ids = []
            documents = []
            metadatas = []
            
            for i, chunk in enumerate(batch):
                clean_src = re.sub(r'[^a-zA-Z0-9_\-]', '_', chunk['metadata']['source'])
                page_idx = chunk['metadata'].get('page', 1)
                chunk_id = f"{clean_src}_p{page_idx}_{start_idx + i}"
                ids.append(chunk_id)
                documents.append(chunk['content'])
                metadatas.append(chunk['metadata'])
            
            self.collection.upsert(
                ids=ids,
                documents=documents,
                metadatas=metadatas
            )
            logger.info(f"Upserted batch {start_idx // batch_size + 1}/{(total + batch_size - 1) // batch_size} ({len(batch)} chunks)")
        
        logger.info(f"Successfully processed {total} chunks in ChromaDB. Total collection size: {self.collection.count()}")

    def query(self, query_text: str, n_results: int = 3) -> Dict[str, Any]:
        """
        Retrieves relevant context for a given mathematical query.
        """
        results = self.collection.query(
            query_texts=[query_text],
            n_results=n_results
        )
        return results

vector_service = VectorService()
