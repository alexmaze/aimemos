"""
Document ingestion pipeline for RAG system.

This module provides functionality to read documents from a local directory,
chunk them using token-based chunking, generate embeddings, and insert them
into the Milvus vector store.
"""

import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import time
import argparse
from tqdm import tqdm

from embeddings import create_embedder, M3EEmbeddings
from vector_store import create_vector_store, MilvusVectorStore


def read_text_file(file_path: str) -> str:
    """
    Read text content from a file.
    
    Args:
        file_path: Path to the text file
        
    Returns:
        Text content as string
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return ""


def chunk_text_by_tokens(
    text: str,
    tokenizer,
    max_tokens: int = 512,
    overlap_tokens: int = 128
) -> List[str]:
    """
    Split text into chunks based on token count with overlap.
    
    Args:
        text: Input text to chunk
        tokenizer: Tokenizer to use for encoding
        max_tokens: Maximum tokens per chunk (default: 512)
        overlap_tokens: Number of overlapping tokens between chunks (default: 128)
        
    Returns:
        List of text chunks
    """
    if not text.strip():
        return []
    
    # Encode the full text
    tokens = tokenizer.encode(text)
    
    chunks = []
    start_idx = 0
    
    while start_idx < len(tokens):
        # Get chunk tokens
        end_idx = min(start_idx + max_tokens, len(tokens))
        chunk_tokens = tokens[start_idx:end_idx]
        
        # Decode back to text
        chunk_text = tokenizer.decode(chunk_tokens, skip_special_tokens=True)
        chunks.append(chunk_text)
        
        # Move to next chunk with overlap
        if end_idx == len(tokens):
            break
        start_idx += max_tokens - overlap_tokens
    
    return chunks


def load_documents_from_directory(
    directory: str,
    extensions: List[str] = ['.txt', '.md']
) -> List[Dict[str, Any]]:
    """
    Load all documents from a directory.
    
    Args:
        directory: Path to the directory containing documents
        extensions: List of file extensions to include (default: ['.txt', '.md'])
        
    Returns:
        List of document dictionaries with 'path' and 'content' keys
    """
    documents = []
    directory_path = Path(directory)
    
    if not directory_path.exists():
        print(f"Warning: Directory {directory} does not exist")
        return documents
    
    print(f"Loading documents from: {directory}")
    
    for ext in extensions:
        for file_path in directory_path.rglob(f'*{ext}'):
            content = read_text_file(str(file_path))
            if content.strip():
                documents.append({
                    'path': str(file_path.relative_to(directory_path)),
                    'full_path': str(file_path),
                    'content': content
                })
    
    print(f"Loaded {len(documents)} documents")
    return documents


def ingest_documents(
    documents: List[Dict[str, Any]],
    embedder: M3EEmbeddings,
    vector_store: MilvusVectorStore,
    kb_id: str = "default",
    max_tokens: int = 512,
    overlap_tokens: int = 128,
    batch_size: int = 32,
    show_progress: bool = True
) -> int:
    """
    Ingest documents into the vector store.
    
    This function chunks documents, generates embeddings, and inserts them
    into the Milvus vector store.
    
    Args:
        documents: List of document dictionaries
        embedder: M3EEmbeddings instance for generating embeddings
        vector_store: MilvusVectorStore instance for storing vectors
        kb_id: Knowledge base identifier (default: "default")
        max_tokens: Maximum tokens per chunk (default: 512)
        overlap_tokens: Overlap between chunks (default: 128)
        batch_size: Batch size for embedding generation (default: 32)
        show_progress: Whether to show progress bar (default: True)
        
    Returns:
        Total number of chunks inserted
    """
    if not documents:
        print("No documents to ingest")
        return 0
    
    print(f"\n=== Starting document ingestion ===")
    print(f"Total documents: {len(documents)}")
    print(f"KB ID: {kb_id}")
    print(f"Chunking params: max_tokens={max_tokens}, overlap={overlap_tokens}")
    
    # Prepare data for insertion
    all_chunks = []
    all_sources = []
    all_metadatas = []
    
    # Step 1: Chunk all documents
    print("\nStep 1: Chunking documents...")
    iterator = tqdm(documents) if show_progress else documents
    
    for doc in iterator:
        chunks = chunk_text_by_tokens(
            doc['content'],
            embedder.tokenizer,
            max_tokens=max_tokens,
            overlap_tokens=overlap_tokens
        )
        
        for chunk in chunks:
            all_chunks.append(chunk)
            all_sources.append(doc['path'])
            all_metadatas.append({
                'kb_id': kb_id,
                'doc_type': 'text',
                'file_path': doc['path'],
                'full_path': doc['full_path']
            })
    
    print(f"Total chunks created: {len(all_chunks)}")
    
    if not all_chunks:
        print("No chunks created, skipping embedding generation")
        return 0
    
    # Step 2: Generate embeddings
    print("\nStep 2: Generating embeddings...")
    embeddings = embedder.embed_texts(
        all_chunks,
        batch_size=batch_size,
        show_progress=show_progress
    )
    
    print(f"Generated {len(embeddings)} embeddings")
    
    # Step 3: Insert into vector store
    print("\nStep 3: Inserting into vector store...")
    
    # Insert in batches
    total_inserted = 0
    insert_batch_size = 100  # Batch size for insertion
    
    for i in range(0, len(all_chunks), insert_batch_size):
        end_idx = min(i + insert_batch_size, len(all_chunks))
        
        batch_embeddings = embeddings[i:end_idx].tolist()
        batch_chunks = all_chunks[i:end_idx]
        batch_sources = all_sources[i:end_idx]
        batch_metadatas = all_metadatas[i:end_idx]
        
        pks = vector_store.insert(
            embeddings=batch_embeddings,
            contents=batch_chunks,
            sources=batch_sources,
            metadatas=batch_metadatas
        )
        
        total_inserted += len(pks)
        
        if show_progress:
            print(f"  Inserted batch {i//insert_batch_size + 1}: {len(pks)} chunks")
    
    print(f"\n=== Ingestion completed ===")
    print(f"Total chunks inserted: {total_inserted}")
    
    return total_inserted


def main():
    """
    Main function for command-line usage.
    """
    parser = argparse.ArgumentParser(
        description='Ingest documents into RAG vector store'
    )
    parser.add_argument(
        '--data-dir',
        type=str,
        default='./data/kb',
        help='Directory containing documents to ingest (default: ./data/kb)'
    )
    parser.add_argument(
        '--kb-id',
        type=str,
        default='default',
        help='Knowledge base identifier (default: default)'
    )
    parser.add_argument(
        '--milvus-uri',
        type=str,
        default='./milvus_demo.db',
        help='Milvus Lite database path (default: ./milvus_demo.db)'
    )
    parser.add_argument(
        '--collection-name',
        type=str,
        default='kb_documents',
        help='Milvus collection name (default: kb_documents)'
    )
    parser.add_argument(
        '--max-tokens',
        type=int,
        default=512,
        help='Maximum tokens per chunk (default: 512)'
    )
    parser.add_argument(
        '--overlap-tokens',
        type=int,
        default=128,
        help='Overlap tokens between chunks (default: 128)'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=32,
        help='Batch size for embedding generation (default: 32)'
    )
    parser.add_argument(
        '--model-name',
        type=str,
        default='moka-ai/m3e-base',
        help='Embedding model name (default: moka-ai/m3e-base)'
    )
    parser.add_argument(
        '--recreate-index',
        action='store_true',
        help='Drop and recreate the collection (WARNING: deletes existing data)'
    )
    
    args = parser.parse_args()
    
    print("=== RAG Document Ingestion Pipeline ===\n")
    print(f"Configuration:")
    print(f"  Data directory: {args.data_dir}")
    print(f"  KB ID: {args.kb_id}")
    print(f"  Milvus URI: {args.milvus_uri}")
    print(f"  Collection: {args.collection_name}")
    print(f"  Model: {args.model_name}")
    print(f"  Max tokens: {args.max_tokens}")
    print(f"  Overlap: {args.overlap_tokens}")
    print(f"  Batch size: {args.batch_size}")
    print()
    
    # Initialize embedder
    print("Initializing embedder...")
    embedder = create_embedder(model_name=args.model_name)
    
    # Initialize vector store
    print("\nInitializing vector store...")
    vector_store = create_vector_store(
        collection_name=args.collection_name,
        embedding_dim=embedder.get_embedding_dim(),
        uri=args.milvus_uri
    )
    
    # Recreate index if requested
    if args.recreate_index:
        print("\nRecreating collection (deleting existing data)...")
        vector_store.drop_collection()
        vector_store.create_collection_if_needed()
    
    # Create index
    print("\nCreating/verifying index...")
    try:
        vector_store.create_index()
    except Exception as e:
        print(f"Index may already exist: {e}")
    
    # Load documents
    print("\nLoading documents...")
    documents = load_documents_from_directory(args.data_dir)
    
    if not documents:
        print(f"\nNo documents found in {args.data_dir}")
        print("Please add some .txt or .md files to the directory")
        return
    
    # Ingest documents
    start_time = time.time()
    total_chunks = ingest_documents(
        documents=documents,
        embedder=embedder,
        vector_store=vector_store,
        kb_id=args.kb_id,
        max_tokens=args.max_tokens,
        overlap_tokens=args.overlap_tokens,
        batch_size=args.batch_size,
        show_progress=True
    )
    elapsed_time = time.time() - start_time
    
    # Show statistics
    print(f"\nIngestion Statistics:")
    print(f"  Total documents: {len(documents)}")
    print(f"  Total chunks: {total_chunks}")
    print(f"  Time elapsed: {elapsed_time:.2f} seconds")
    print(f"  Chunks/second: {total_chunks/elapsed_time:.2f}")
    
    # Show collection stats
    stats = vector_store.get_stats()
    print(f"\nCollection Statistics:")
    print(f"  Name: {stats['name']}")
    print(f"  Total entities: {stats['num_entities']}")
    
    # Disconnect
    vector_store.disconnect()
    print("\nIngestion completed successfully!")


if __name__ == "__main__":
    main()
