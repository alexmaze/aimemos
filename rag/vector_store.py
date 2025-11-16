"""
Milvus Lite vector store operations wrapper.

This module provides a clean interface for working with Milvus Lite,
including connection management, collection creation, indexing, and
search operations.
"""

from typing import List, Dict, Any, Optional, Tuple
from pymilvus import (
    connections,
    Collection,
    CollectionSchema,
    FieldSchema,
    DataType,
    utility
)
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MilvusVectorStore:
    """
    Wrapper for Milvus Lite vector database operations.
    
    Provides methods for collection management, data insertion, and
    similarity search with support for metadata filtering.
    
    Attributes:
        collection_name (str): Name of the Milvus collection
        embedding_dim (int): Dimension of embedding vectors
        collection (Collection): Milvus collection instance
    """
    
    def __init__(
        self,
        collection_name: str = "kb_documents",
        embedding_dim: int = 768,
        uri: str = "./milvus_demo.db"
    ):
        """
        Initialize Milvus vector store.
        
        Args:
            collection_name: Name of the collection to use
            embedding_dim: Dimension of embedding vectors (default: 768 for m3e-base)
            uri: Path to Milvus Lite database file
        """
        self.collection_name = collection_name
        self.embedding_dim = embedding_dim
        self.uri = uri
        self.collection = None
        
        logger.info(f"Initializing Milvus vector store: {collection_name}")
    
    def connect(self) -> None:
        """
        Connect to Milvus Lite database.
        
        Creates a connection using the specified URI (local file path).
        """
        logger.info(f"Connecting to Milvus Lite: {self.uri}")
        
        connections.connect(
            alias="default",
            uri=self.uri
        )
        
        logger.info("Connected to Milvus Lite successfully")
    
    def disconnect(self) -> None:
        """
        Disconnect from Milvus database.
        """
        connections.disconnect("default")
        logger.info("Disconnected from Milvus")
    
    def _create_schema(self) -> CollectionSchema:
        """
        Create collection schema for knowledge base documents.
        
        Returns:
            CollectionSchema with fields: pk, embedding, content, source, metadata, created_at
        """
        fields = [
            FieldSchema(
                name="pk",
                dtype=DataType.INT64,
                is_primary=True,
                auto_id=True,
                description="Primary key"
            ),
            FieldSchema(
                name="embedding",
                dtype=DataType.FLOAT_VECTOR,
                dim=self.embedding_dim,
                description="Document chunk embedding vector"
            ),
            FieldSchema(
                name="content",
                dtype=DataType.VARCHAR,
                max_length=65535,
                description="Original text content"
            ),
            FieldSchema(
                name="source",
                dtype=DataType.VARCHAR,
                max_length=512,
                description="Document source path or identifier"
            ),
            FieldSchema(
                name="metadata",
                dtype=DataType.JSON,
                description="Metadata (kb_id, doc_type, tags, etc.)"
            ),
            FieldSchema(
                name="created_at",
                dtype=DataType.INT64,
                description="Creation timestamp in milliseconds"
            )
        ]
        
        schema = CollectionSchema(
            fields=fields,
            description="Knowledge base documents collection"
        )
        
        return schema
    
    def create_collection_if_needed(self) -> None:
        """
        Create collection if it doesn't exist.
        
        Checks if the collection exists and creates it with proper schema
        if not found.
        """
        if utility.has_collection(self.collection_name):
            logger.info(f"Collection '{self.collection_name}' already exists")
            self.collection = Collection(self.collection_name)
        else:
            logger.info(f"Creating collection: {self.collection_name}")
            schema = self._create_schema()
            self.collection = Collection(
                name=self.collection_name,
                schema=schema
            )
            logger.info(f"Collection '{self.collection_name}' created successfully")
    
    def create_index(
        self,
        field_name: str = "embedding",
        index_type: str = "IVF_FLAT",
        metric_type: str = "L2",
        nlist: int = 128
    ) -> None:
        """
        Create index on the embedding field.
        
        Args:
            field_name: Name of the field to index (default: "embedding")
            index_type: Type of index (default: "IVF_FLAT")
            metric_type: Distance metric (default: "L2")
            nlist: Number of cluster units (default: 128)
        """
        if self.collection is None:
            raise ValueError("Collection not initialized. Call create_collection_if_needed first.")
        
        logger.info(f"Creating index on field '{field_name}'")
        
        index_params = {
            "metric_type": metric_type,
            "index_type": index_type,
            "params": {"nlist": nlist}
        }
        
        self.collection.create_index(
            field_name=field_name,
            index_params=index_params
        )
        
        logger.info("Index created successfully")
    
    def insert(
        self,
        embeddings: List[List[float]],
        contents: List[str],
        sources: List[str],
        metadatas: List[Dict[str, Any]],
        created_ats: Optional[List[int]] = None
    ) -> List[int]:
        """
        Insert documents into the collection.
        
        Args:
            embeddings: List of embedding vectors
            contents: List of text contents
            sources: List of source identifiers
            metadatas: List of metadata dictionaries
            created_ats: List of creation timestamps (auto-generated if None)
            
        Returns:
            List of inserted primary keys
        """
        if self.collection is None:
            raise ValueError("Collection not initialized. Call create_collection_if_needed first.")
        
        # Validate input lengths
        n = len(embeddings)
        if not (len(contents) == len(sources) == len(metadatas) == n):
            raise ValueError("All input lists must have the same length")
        
        # Generate timestamps if not provided
        if created_ats is None:
            current_time = int(time.time() * 1000)
            created_ats = [current_time] * n
        
        # Prepare data
        data = [
            embeddings,
            contents,
            sources,
            metadatas,
            created_ats
        ]
        
        logger.info(f"Inserting {n} documents into collection")
        
        # Insert data
        insert_result = self.collection.insert(data)
        
        # Flush to ensure data is persisted
        self.collection.flush()
        
        logger.info(f"Inserted {n} documents successfully")
        
        return insert_result.primary_keys
    
    def search(
        self,
        query_embeddings: List[List[float]],
        top_k: int = 5,
        output_fields: Optional[List[str]] = None,
        filter_expr: Optional[str] = None,
        nprobe: int = 10
    ) -> List[List[Dict[str, Any]]]:
        """
        Search for similar documents.
        
        Args:
            query_embeddings: List of query embedding vectors
            top_k: Number of results to return per query (default: 5)
            output_fields: Fields to include in results (default: all)
            filter_expr: Metadata filter expression (default: None)
            nprobe: Number of clusters to search (default: 10)
            
        Returns:
            List of search results for each query, where each result is a list of dicts
            containing the matched documents and their distances
        """
        if self.collection is None:
            raise ValueError("Collection not initialized. Call create_collection_if_needed first.")
        
        # Load collection into memory
        self.collection.load()
        
        # Set default output fields
        if output_fields is None:
            output_fields = ["content", "source", "metadata", "created_at"]
        
        # Search parameters
        search_params = {
            "metric_type": "L2",
            "params": {"nprobe": nprobe}
        }
        
        logger.info(f"Searching for {len(query_embeddings)} queries, top_k={top_k}")
        
        # Perform search
        results = self.collection.search(
            data=query_embeddings,
            anns_field="embedding",
            param=search_params,
            limit=top_k,
            expr=filter_expr,
            output_fields=output_fields
        )
        
        # Format results
        formatted_results = []
        for hits in results:
            query_results = []
            for hit in hits:
                result = {
                    "id": hit.id,
                    "distance": hit.distance,
                    "score": 1.0 / (1.0 + hit.distance)  # Convert distance to similarity score
                }
                # Add output fields
                for field in output_fields:
                    result[field] = hit.entity.get(field)
                query_results.append(result)
            formatted_results.append(query_results)
        
        logger.info(f"Search completed, found {len(formatted_results)} result sets")
        
        return formatted_results
    
    def delete(
        self,
        filter_expr: str
    ) -> int:
        """
        Delete documents matching the filter expression.
        
        Args:
            filter_expr: Boolean expression for filtering (e.g., 'pk in [1,2,3]')
            
        Returns:
            Number of deleted entities
        """
        if self.collection is None:
            raise ValueError("Collection not initialized. Call create_collection_if_needed first.")
        
        logger.info(f"Deleting documents with filter: {filter_expr}")
        
        result = self.collection.delete(filter_expr)
        self.collection.flush()
        
        logger.info(f"Deleted {result.delete_count} documents")
        
        return result.delete_count
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get collection statistics.
        
        Returns:
            Dictionary containing collection stats (entity count, etc.)
        """
        if self.collection is None:
            raise ValueError("Collection not initialized. Call create_collection_if_needed first.")
        
        stats = {
            "name": self.collection_name,
            "num_entities": self.collection.num_entities,
            "schema": str(self.collection.schema)
        }
        
        return stats
    
    def drop_collection(self) -> None:
        """
        Drop the collection (WARNING: This deletes all data).
        """
        if self.collection is None:
            logger.warning("Collection not initialized, nothing to drop")
            return
        
        logger.warning(f"Dropping collection: {self.collection_name}")
        utility.drop_collection(self.collection_name)
        self.collection = None
        logger.info("Collection dropped successfully")


def create_vector_store(
    collection_name: str = "kb_documents",
    embedding_dim: int = 768,
    uri: str = "./milvus_demo.db"
) -> MilvusVectorStore:
    """
    Factory function to create and initialize a Milvus vector store.
    
    Args:
        collection_name: Name of the collection
        embedding_dim: Dimension of embedding vectors
        uri: Path to Milvus Lite database file
        
    Returns:
        Initialized MilvusVectorStore instance
    """
    store = MilvusVectorStore(
        collection_name=collection_name,
        embedding_dim=embedding_dim,
        uri=uri
    )
    store.connect()
    store.create_collection_if_needed()
    
    return store


if __name__ == "__main__":
    # Example usage
    import numpy as np
    
    print("=== Milvus Vector Store Example ===\n")
    
    # Create vector store
    store = create_vector_store()
    
    # Create index
    store.create_index()
    
    # Insert sample data
    n_docs = 5
    embeddings = np.random.randn(n_docs, 768).tolist()
    contents = [f"这是第 {i+1} 个文档的内容" for i in range(n_docs)]
    sources = [f"doc_{i+1}.txt" for i in range(n_docs)]
    metadatas = [{"kb_id": "test_kb", "doc_type": "text"} for _ in range(n_docs)]
    
    pks = store.insert(
        embeddings=embeddings,
        contents=contents,
        sources=sources,
        metadatas=metadatas
    )
    
    print(f"Inserted {len(pks)} documents")
    print(f"Primary keys: {pks[:3]}...\n")
    
    # Get stats
    stats = store.get_stats()
    print(f"Collection stats: {stats}\n")
    
    # Search
    query_embedding = np.random.randn(1, 768).tolist()
    results = store.search(
        query_embeddings=query_embedding,
        top_k=3
    )
    
    print(f"Search results for query:")
    for i, result in enumerate(results[0]):
        print(f"  {i+1}. Content: {result['content'][:50]}...")
        print(f"     Score: {result['score']:.4f}")
        print(f"     Source: {result['source']}")
    
    # Disconnect
    store.disconnect()
    print("\nExample completed successfully!")
