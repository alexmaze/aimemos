"""
RAG (Retrieval-Augmented Generation) Module

This package provides components for building a RAG system including:
- Embeddings: Chinese text embedding using moka-ai/m3e-base
- Vector Store: Milvus Lite vector database operations
- Ingest: Document processing and indexing pipeline
- LLM Client: OpenAI-compatible local LLM interface

For usage instructions, see rag/README.md
For design details, see rag/DESIGN_RAG.md
"""

__version__ = "1.0.0"
__author__ = "AIMemos Team"

from .embeddings import M3EEmbeddings, create_embedder
from .vector_store import MilvusVectorStore, create_vector_store
from .llm_client import LLMClient, create_llm_client

__all__ = [
    "M3EEmbeddings",
    "create_embedder",
    "MilvusVectorStore",
    "create_vector_store",
    "LLMClient",
    "create_llm_client",
]
