"""
GPU-accelerated embeddings generation using sentence-transformers.

This module provides embeddings for:
- Entities (for semantic similarity search)
- Document chunks (for similarity matching)
- Custom text embeddings (for classification, clustering, etc.)
"""
import torch
from typing import List, Optional, Union
import logging
from sentence_transformers import SentenceTransformer
import numpy as np

logger = logging.getLogger(__name__)

# Global models cache
_embedding_model: Optional[SentenceTransformer] = None


def get_embedding_model(
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
    device: Optional[str] = None,
    batch_size: int = 32
) -> SentenceTransformer:
    """
    Get or create GPU-accelerated embedding model.
    
    Args:
        model_name: Sentence transformer model name
        device: Device to use ('cuda', 'cpu', or None for auto-detection)
        batch_size: Batch size for encoding
        
    Returns:
        SentenceTransformer model loaded and ready for use
    """
    global _embedding_model
    
    # Return cached model if available
    if _embedding_model is not None:
        return _embedding_model
    
    logger.info(f"Loading embedding model: {model_name}")
    
    # Auto-detect device if not specified
    if device is None:
        if torch.cuda.is_available():
            device = "cuda"
            logger.info(f"GPU available - using CUDA device {torch.cuda.current_device()}")
        else:
            device = "cpu"
            logger.info("GPU not available - using CPU")
    
    try:
        # Load model
        model = SentenceTransformer(model_name, device=device)
        
        # Store device info in model metadata (device is read-only property)
        model._model_device = device
        model._model_name = model_name
        model._batch_size = batch_size
        
        # Cache the model
        _embedding_model = model
        
        logger.info(f"Embedding model loaded successfully on {device}")
        
        return model
        
    except Exception as e:
        logger.error(f"Failed to load embedding model: {e}")
        raise


def generate_embeddings(
    texts: Union[str, List[str]],
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
    batch_size: int = 32,
    show_progress: bool = False,
    normalize_embeddings: bool = True
) -> np.ndarray:
    """
    Generate embeddings for text(s) using GPU acceleration.
    
    Args:
        texts: Single text string or list of texts
        model_name: Model to use for embeddings
        batch_size: Batch size for processing
        show_progress: Show progress bar
        normalize_embeddings: Normalize embeddings to unit length
        
    Returns:
        numpy array of embeddings (384-dimensional for all-MiniLM-L6-v2)
    """
    # Get embedding model
    model = get_embedding_model(model_name=model_name, batch_size=batch_size)
    
    # Handle single text vs list
    if isinstance(texts, str):
        texts = [texts]
        single_text = True
    else:
        single_text = False
    
    try:
        # Generate embeddings
        embeddings = model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=show_progress,
            normalize_embeddings=normalize_embeddings,
            convert_to_numpy=True
        )
        
        # Return single embedding or array
        if single_text:
            return embeddings[0]
        return embeddings
        
    except Exception as e:
        logger.error(f"Failed to generate embeddings: {e}")
        raise


def generate_entity_embeddings(
    entities: List[dict],
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
) -> List[dict]:
    """
    Generate embeddings for a list of entities.
    
    Args:
        entities: List of entity dicts with 'surface' and 'type' fields
        model_name: Model to use for embeddings
        
    Returns:
        List of entities with 'embedding' field added
    """
    # Extract texts for embedding
    entity_texts = []
    for entity in entities:
        # Combine entity type and surface form for better embeddings
        text = f"{entity.get('type', 'ENTITY')}: {entity.get('surface', '')}"
        entity_texts.append(text)
    
    # Generate embeddings in batch
    embeddings = generate_embeddings(
        entity_texts,
        model_name=model_name,
        show_progress=len(entities) > 100
    )
    
    # Add embeddings to entities
    for i, entity in enumerate(entities):
        entity['embedding'] = embeddings[i].tolist()  # Convert to list for JSON serialization
        entity['embedding_model'] = model_name
        entity['embedding_dim'] = len(embeddings[i])
    
    return entities


def generate_chunk_embeddings(
    chunks: List[dict],
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
) -> List[dict]:
    """
    Generate embeddings for document chunks.
    
    Args:
        chunks: List of chunk dicts with 'text' field
        model_name: Model to use for embeddings
        
    Returns:
        List of chunks with 'embedding' field added
    """
    # Extract texts
    chunk_texts = [chunk.get('text', '') for chunk in chunks]
    
    # Generate embeddings in batch
    embeddings = generate_embeddings(
        chunk_texts,
        model_name=model_name,
        show_progress=len(chunks) > 50
    )
    
    # Add embeddings to chunks
    for i, chunk in enumerate(chunks):
        chunk['embedding'] = embeddings[i].tolist()
        chunk['embedding_model'] = model_name
        chunk['embedding_dim'] = len(embeddings[i])
    
    return chunks


def get_embedding_info() -> dict:
    """
    Get information about the loaded embedding model.
    
    Returns:
        Dict with model info (device, model_name, batch_size, etc.)
    """
    if _embedding_model is None:
        return {
            "loaded": False,
            "device": None,
            "model_name": None
        }
    
    info = {
        "loaded": True,
        "device": getattr(_embedding_model, '_model_device', getattr(_embedding_model, 'device', None)),
        "model_name": getattr(_embedding_model, '_model_name', None),
        "batch_size": getattr(_embedding_model, '_batch_size', None),
        "max_seq_length": getattr(_embedding_model, 'max_seq_length', None)
    }
    
    # Add GPU info if using CUDA
    if info["device"] == "cuda":
        info["gpu_device"] = torch.cuda.current_device()
        info["gpu_name"] = torch.cuda.get_device_name()
        info["gpu_memory_allocated"] = torch.cuda.memory_allocated() / (1024**3)
        info["gpu_memory_reserved"] = torch.cuda.memory_reserved() / (1024**3)
    
    return info


def clear_embedding_cache():
    """
    Clear the cached embedding model and free GPU memory.
    Useful for memory management or when switching models.
    """
    global _embedding_model
    
    if _embedding_model is not None:
        logger.info("Clearing embedding model cache")
        
        # Free GPU memory if using CUDA
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        _embedding_model = None
        logger.info("Embedding model cache cleared")


def get_model_dimension(model_name: str = "sentence-transformers/all-MiniLM-L6-v2") -> int:
    """
    Get the embedding dimension for a given model without loading it.
    
    Args:
        model_name: Model name
        
    Returns:
        Embedding dimension
    """
    # Common model dimensions
    model_dims = {
        "sentence-transformers/all-MiniLM-L6-v2": 384,
        "sentence-transformers/all-mpnet-base-v2": 768,
        "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2": 384,
    }
    
    return model_dims.get(model_name, 384)

