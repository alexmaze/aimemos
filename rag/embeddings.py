"""
Embedding service using moka-ai/m3e-base model.

This module provides a wrapper for the m3e-base Chinese embedding model
using Hugging Face Transformers. It supports batch embedding generation
with automatic L2 normalization.
"""

import torch
from transformers import AutoTokenizer, AutoModel
from typing import List, Optional
import numpy as np


class M3EEmbeddings:
    """
    Wrapper for moka-ai/m3e-base embedding model.
    
    This class handles loading the model, tokenization, and embedding generation
    with automatic L2 normalization for better similarity computation.
    
    Attributes:
        model_name (str): Hugging Face model identifier
        device (str): Device to run the model on ('cuda' or 'cpu')
        tokenizer: Hugging Face tokenizer
        model: Hugging Face model
        embedding_dim (int): Dimension of the embedding vectors
    """
    
    def __init__(
        self,
        model_name: str = "moka-ai/m3e-base",
        device: Optional[str] = None,
        cache_dir: Optional[str] = None
    ):
        """
        Initialize the M3E embedding model.
        
        Args:
            model_name: Hugging Face model identifier (default: moka-ai/m3e-base)
            device: Device to use ('cuda' or 'cpu'). Auto-detected if None.
            cache_dir: Directory to cache downloaded models
        """
        self.model_name = model_name
        
        # Auto-detect device if not specified
        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device
        
        print(f"Loading tokenizer and model: {model_name}")
        print(f"Using device: {self.device}")
        
        # Load tokenizer and model
        self.tokenizer = AutoTokenizer.from_pretrained(
            model_name,
            cache_dir=cache_dir,
            trust_remote_code=True
        )
        
        self.model = AutoModel.from_pretrained(
            model_name,
            cache_dir=cache_dir,
            trust_remote_code=True
        )
        
        # Move model to device
        self.model.to(self.device)
        self.model.eval()
        
        # Get embedding dimension by doing a test forward pass
        with torch.no_grad():
            test_input = self.tokenizer(
                "测试文本",
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=512
            ).to(self.device)
            test_output = self.model(**test_input)
            # Use mean pooling of last hidden state
            self.embedding_dim = test_output.last_hidden_state.mean(dim=1).shape[-1]
        
        print(f"Model loaded successfully. Embedding dimension: {self.embedding_dim}")
    
    def get_embedding_dim(self) -> int:
        """
        Get the dimension of the embedding vectors.
        
        Returns:
            int: Embedding dimension (768 for m3e-base)
        """
        return self.embedding_dim
    
    def _mean_pooling(
        self,
        model_output,
        attention_mask
    ) -> torch.Tensor:
        """
        Apply mean pooling to model output.
        
        Args:
            model_output: Model output containing last_hidden_state
            attention_mask: Attention mask for the input
            
        Returns:
            Pooled embeddings
        """
        token_embeddings = model_output.last_hidden_state
        input_mask_expanded = (
            attention_mask.unsqueeze(-1)
            .expand(token_embeddings.size())
            .float()
        )
        sum_embeddings = torch.sum(token_embeddings * input_mask_expanded, 1)
        sum_mask = torch.clamp(input_mask_expanded.sum(1), min=1e-9)
        return sum_embeddings / sum_mask
    
    def _normalize_embeddings(
        self,
        embeddings: torch.Tensor
    ) -> torch.Tensor:
        """
        Apply L2 normalization to embeddings.
        
        Args:
            embeddings: Input embeddings
            
        Returns:
            L2-normalized embeddings
        """
        return torch.nn.functional.normalize(embeddings, p=2, dim=1)
    
    def embed_text(
        self,
        text: str,
        normalize: bool = True
    ) -> np.ndarray:
        """
        Generate embedding for a single text.
        
        Args:
            text: Input text string
            normalize: Whether to apply L2 normalization (default: True)
            
        Returns:
            numpy array of shape (embedding_dim,)
        """
        return self.embed_texts([text], normalize=normalize)[0]
    
    def embed_texts(
        self,
        texts: List[str],
        batch_size: int = 32,
        normalize: bool = True,
        show_progress: bool = False
    ) -> np.ndarray:
        """
        Generate embeddings for multiple texts in batches.
        
        Args:
            texts: List of text strings
            batch_size: Batch size for processing (default: 32)
            normalize: Whether to apply L2 normalization (default: True)
            show_progress: Whether to show progress bar (default: False)
            
        Returns:
            numpy array of shape (len(texts), embedding_dim)
        """
        all_embeddings = []
        
        # Setup progress bar if requested
        if show_progress:
            from tqdm import tqdm
            iterator = tqdm(
                range(0, len(texts), batch_size),
                desc="Generating embeddings"
            )
        else:
            iterator = range(0, len(texts), batch_size)
        
        with torch.no_grad():
            for i in iterator:
                batch_texts = texts[i:i + batch_size]
                
                # Tokenize batch
                encoded_input = self.tokenizer(
                    batch_texts,
                    padding=True,
                    truncation=True,
                    max_length=512,
                    return_tensors="pt"
                ).to(self.device)
                
                # Forward pass
                model_output = self.model(**encoded_input)
                
                # Apply mean pooling
                embeddings = self._mean_pooling(
                    model_output,
                    encoded_input['attention_mask']
                )
                
                # Apply L2 normalization if requested
                if normalize:
                    embeddings = self._normalize_embeddings(embeddings)
                
                # Move to CPU and convert to numpy
                all_embeddings.append(embeddings.cpu().numpy())
        
        # Concatenate all batches
        return np.vstack(all_embeddings)
    
    def __call__(
        self,
        texts: List[str],
        **kwargs
    ) -> np.ndarray:
        """
        Callable interface for embedding generation.
        
        Args:
            texts: List of text strings
            **kwargs: Additional arguments passed to embed_texts
            
        Returns:
            numpy array of embeddings
        """
        return self.embed_texts(texts, **kwargs)


def create_embedder(
    model_name: str = "moka-ai/m3e-base",
    device: Optional[str] = None,
    cache_dir: Optional[str] = None
) -> M3EEmbeddings:
    """
    Factory function to create an M3E embedder instance.
    
    Args:
        model_name: Hugging Face model identifier
        device: Device to use ('cuda' or 'cpu')
        cache_dir: Directory to cache downloaded models
        
    Returns:
        M3EEmbeddings instance
    """
    return M3EEmbeddings(
        model_name=model_name,
        device=device,
        cache_dir=cache_dir
    )


if __name__ == "__main__":
    # Example usage
    print("=== M3E Embeddings Example ===\n")
    
    # Create embedder
    embedder = create_embedder()
    
    # Single text embedding
    text = "这是一个测试文本"
    embedding = embedder.embed_text(text)
    print(f"Text: {text}")
    print(f"Embedding shape: {embedding.shape}")
    print(f"Embedding (first 5 dims): {embedding[:5]}")
    print(f"L2 norm: {np.linalg.norm(embedding):.4f}\n")
    
    # Batch embedding
    texts = [
        "人工智能是计算机科学的一个分支",
        "机器学习是人工智能的核心技术",
        "深度学习使用神经网络进行学习",
        "自然语言处理研究计算机与人类语言的交互"
    ]
    
    embeddings = embedder.embed_texts(texts, show_progress=True)
    print(f"\nBatch embeddings shape: {embeddings.shape}")
    
    # Compute similarity between first two texts
    similarity = np.dot(embeddings[0], embeddings[1])
    print(f"\nSimilarity between first two texts: {similarity:.4f}")
