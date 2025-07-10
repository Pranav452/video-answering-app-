import os
import logging
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime

# LangChain imports
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain_community.vectorstores import Chroma

# Sentence transformers for embeddings
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.utils import embedding_functions

logger = logging.getLogger(__name__)

class RAGPipeline:
    """
    Handles RAG pipeline for transcript processing and retrieval
    """
    
    def __init__(self):
        # Initialize sentence transformer model for embeddings
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Initialize ChromaDB client
        self.chroma_client = chromadb.PersistentClient(path="./chroma_db")
        
        # Create embedding function for ChromaDB
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        
        # Initialize text splitter for chunking
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,  # Size of each chunk
            chunk_overlap=200,  # Overlap between chunks
            length_function=len,
            separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""]
        )
        
        logger.info("RAG pipeline initialized successfully")
    
    async def process_transcript(self, transcript: Dict[str, Any], video_id: str) -> None:
        """
        Process transcript through RAG pipeline
        
        Args:
            transcript: Transcript data with segments and timestamps
            video_id: Unique identifier for the video
        """
        try:
            # Create or get collection for this video
            collection_name = f"video_{video_id}"
            
            # Delete existing collection if it exists
            try:
                self.chroma_client.delete_collection(collection_name)
            except:
                pass  # Collection doesn't exist, which is fine
            
            # Create new collection
            collection = self.chroma_client.create_collection(
                name=collection_name,
                embedding_function=self.embedding_function
            )
            
            # Process transcript segments into chunks
            chunks = await self._create_chunks_with_timestamps(transcript)
            
            # Add chunks to vector store
            await self._add_chunks_to_collection(collection, chunks)
            
            logger.info(f"Processed {len(chunks)} chunks for video {video_id}")
            
        except Exception as e:
            logger.error(f"RAG pipeline error: {e}")
            raise Exception(f"RAG processing failed: {e}")
    
    async def _create_chunks_with_timestamps(self, transcript: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Create chunks from transcript while preserving timestamps
        
        Args:
            transcript: Transcript data with segments
            
        Returns:
            List of chunks with metadata
        """
        chunks = []
        
        # Combine all segments into full text for better chunking
        full_text = " ".join([segment["text"] for segment in transcript["segments"]])
        
        # Split text into chunks
        text_chunks = self.text_splitter.split_text(full_text)
        
        for i, chunk_text in enumerate(text_chunks):
            # Find corresponding timestamp for this chunk
            start_time, end_time = self._find_chunk_timestamps(chunk_text, transcript)
            
            chunk = {
                "text": chunk_text,
                "chunk_id": i,
                "start_time": start_time,
                "end_time": end_time,
                "duration": end_time - start_time if end_time > start_time else 0.0,
                "language": transcript.get("language", "en")
            }
            
            chunks.append(chunk)
        
        return chunks
    
    def _find_chunk_timestamps(self, chunk_text: str, transcript: Dict[str, Any]) -> tuple[float, float]:
        """
        Find start and end timestamps for a text chunk
        
        Args:
            chunk_text: Text content of the chunk
            transcript: Full transcript with segments
            
        Returns:
            Tuple of (start_time, end_time)
        """
        # Find the first few words of the chunk in the transcript
        chunk_words = chunk_text.split()[:5]  # Use first 5 words for matching
        first_words = " ".join(chunk_words)
        
        # Find the last few words of the chunk
        last_words = " ".join(chunk_text.split()[-5:])
        
        start_time = 0.0
        end_time = 0.0
        
        # Search through transcript segments
        for segment in transcript["segments"]:
            segment_text = segment["text"].strip()
            
            # Check if this segment contains the start of our chunk
            if first_words.lower() in segment_text.lower() and start_time == 0.0:
                start_time = segment["start"]
            
            # Check if this segment contains the end of our chunk
            if last_words.lower() in segment_text.lower():
                end_time = segment["end"]
        
        # If we couldn't find exact matches, estimate based on position
        if start_time == 0.0 or end_time == 0.0:
            # Calculate approximate position based on text length
            full_text = " ".join([seg["text"] for seg in transcript["segments"]])
            chunk_start_pos = full_text.find(chunk_text)
            
            if chunk_start_pos != -1:
                # Estimate timestamp based on text position
                total_duration = transcript.get("duration", 0.0)
                if total_duration > 0:
                    relative_position = chunk_start_pos / len(full_text)
                    start_time = relative_position * total_duration
                    end_time = min(start_time + 30.0, total_duration)  # Assume 30 second chunks
        
        return start_time, end_time
    
    async def _add_chunks_to_collection(self, collection, chunks: List[Dict[str, Any]]) -> None:
        """
        Add chunks to ChromaDB collection
        
        Args:
            collection: ChromaDB collection
            chunks: List of chunks with metadata
        """
        # Prepare data for ChromaDB
        texts = [chunk["text"] for chunk in chunks]
        metadatas = [
            {
                "chunk_id": chunk["chunk_id"],
                "start_time": chunk["start_time"],
                "end_time": chunk["end_time"],
                "duration": chunk["duration"],
                "language": chunk["language"]
            }
            for chunk in chunks
        ]
        ids = [f"chunk_{i}" for i in range(len(chunks))]
        
        # Add to collection
        collection.add(
            documents=texts,
            metadatas=metadatas,
            ids=ids
        )
    
    async def search_relevant_chunks(self, query: str, video_id: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search for relevant chunks based on query
        
        Args:
            query: Search query
            video_id: Video identifier
            top_k: Number of top results to return
            
        Returns:
            List of relevant chunks with metadata
        """
        try:
            collection_name = f"video_{video_id}"
            collection = self.chroma_client.get_collection(
                name=collection_name,
                embedding_function=self.embedding_function
            )
            
            # Search for relevant chunks
            results = collection.query(
                query_texts=[query],
                n_results=top_k
            )
            
            # Process results
            relevant_chunks = []
            if results["documents"] and results["documents"][0]:
                for i, doc in enumerate(results["documents"][0]):
                    metadata = results["metadatas"][0][i]
                    distance = results["distances"][0][i] if results["distances"] else 0.0
                    
                    chunk = {
                        "text": doc,
                        "metadata": metadata,
                        "relevance_score": 1.0 - distance,  # Convert distance to similarity score
                        "start_time": metadata["start_time"],
                        "end_time": metadata["end_time"]
                    }
                    relevant_chunks.append(chunk)
            
            return relevant_chunks
            
        except Exception as e:
            logger.error(f"Search error: {e}")
            raise Exception(f"Search failed: {e}")
    
    def get_collection_info(self, video_id: str) -> Dict[str, Any]:
        """
        Get information about a video's collection
        
        Args:
            video_id: Video identifier
            
        Returns:
            Collection information
        """
        try:
            collection_name = f"video_{video_id}"
            collection = self.chroma_client.get_collection(
                name=collection_name,
                embedding_function=self.embedding_function
            )
            
            count = collection.count()
            
            return {
                "collection_name": collection_name,
                "chunk_count": count,
                "status": "ready"
            }
            
        except Exception as e:
            logger.error(f"Collection info error: {e}")
            return {
                "collection_name": f"video_{video_id}",
                "chunk_count": 0,
                "status": "not_found"
            } 