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

    async def add_documents(self, chunks: List[Dict[str, Any]]):
        """
        Adds parsed chunks to the vector database.
        """
        ids = [f"{chunk['metadata']['source']}_p{chunk['metadata']['page']}_{i}" for i, chunk in enumerate(chunks)]
        documents = [chunk['content'] for chunk in chunks]
        metadatas = [chunk['metadata'] for chunk in chunks]
        
        self.collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )
        logger.info(f"Added {len(chunks)} chunks to ChromaDB.")

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
