import os
import logging
from typing import Dict, List, Any, Optional
import asyncio
from datetime import datetime

# Google Gemini API
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

from .rag_pipeline import RAGPipeline

logger = logging.getLogger(__name__)

class ChatService:
    """
    Handles chat interactions with lecture content using RAG + Gemini
    """
    
    def __init__(self, rag_pipeline: RAGPipeline):
        self.rag_pipeline = rag_pipeline
        
        # Initialize Gemini API - API key should be set in environment
        # Required environment variable: GEMINI_API_KEY
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            logger.warning("GEMINI_API_KEY not found in environment variables")
        
        genai.configure(api_key=api_key)
        
        # Initialize Gemini model (using Gemini 1.5 Pro for better context understanding)
        self.model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            safety_settings={
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            }
        )
        
        logger.info("Chat service initialized successfully")
    
    async def get_response(self, query: str, video_id: str) -> Dict[str, Any]:
        """
        Get intelligent response to user query using RAG + Gemini
        
        Args:
            query: User's question
            video_id: Video identifier
            
        Returns:
            Response with answer and relevant timestamps
        """
        try:
            # Step 1: Retrieve relevant chunks from RAG pipeline
            relevant_chunks = await self.rag_pipeline.search_relevant_chunks(
                query=query, 
                video_id=video_id, 
                top_k=5
            )
            
            if not relevant_chunks:
                return {
                    "response": "I couldn't find relevant information in the lecture for your question. Could you try rephrasing or asking about a different topic?",
                    "timestamps": [],
                    "confidence": 0.0
                }
            
            # Step 2: Prepare context for Gemini
            context = self._prepare_context(relevant_chunks)
            
            # Step 3: Generate response using Gemini
            response_text = await self._generate_response(query, context)
            
            # Step 4: Extract timestamps from relevant chunks
            timestamps = self._extract_timestamps(relevant_chunks)
            
            # Step 5: Calculate confidence score
            confidence = self._calculate_confidence(relevant_chunks)
            
            return {
                "response": response_text,
                "timestamps": timestamps,
                "confidence": confidence
            }
            
        except Exception as e:
            logger.error(f"Chat service error: {e}")
            return {
                "response": "I apologize, but I encountered an error while processing your question. Please try again.",
                "timestamps": [],
                "confidence": 0.0
            }
    
    def _prepare_context(self, chunks: List[Dict[str, Any]]) -> str:
        """
        Prepare context string from relevant chunks
        
        Args:
            chunks: List of relevant chunks
            
        Returns:
            Formatted context string
        """
        context_parts = []
        
        for i, chunk in enumerate(chunks):
            start_time = self._format_timestamp(chunk["start_time"])
            end_time = self._format_timestamp(chunk["end_time"])
            
            context_part = f"""
[Timestamp: {start_time} - {end_time}]
{chunk["text"]}
"""
            context_parts.append(context_part)
        
        return "\n".join(context_parts)
    
    async def _generate_response(self, query: str, context: str) -> str:
        """
        Generate response using Gemini API
        
        Args:
            query: User's question
            context: Relevant context from lecture
            
        Returns:
            Generated response
        """
        prompt = f"""
You are an intelligent teaching assistant helping students understand lecture content. 
Based on the provided lecture transcript segments with timestamps, answer the student's question accurately and helpfully.

LECTURE CONTEXT:
{context}

STUDENT QUESTION: {query}

Instructions:
1. Answer the question based ONLY on the provided lecture context
2. If the question asks about specific timestamps, reference them in your answer
3. If the context doesn't contain enough information to answer fully, say so
4. Be conversational and educational in your tone
5. When referencing specific points, mention the approximate timestamp
6. If asked for examples or explanations, provide them from the lecture content

ANSWER:
"""
        
        try:
            # Generate response using Gemini
            response = await asyncio.get_event_loop().run_in_executor(
                None, 
                self.model.generate_content, 
                prompt
            )
            
            return response.text
            
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            return "I apologize, but I couldn't generate a response at this time. Please try again."
    
    def _extract_timestamps(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, float]]:
        """
        Extract timestamps from relevant chunks
        
        Args:
            chunks: List of relevant chunks
            
        Returns:
            List of timestamp dictionaries
        """
        timestamps = []
        
        for chunk in chunks:
            timestamp = {
                "start": chunk["start_time"],
                "end": chunk["end_time"],
                "relevance": chunk.get("relevance_score", 0.0)
            }
            timestamps.append(timestamp)
        
        # Sort by relevance (highest first)
        timestamps.sort(key=lambda x: x["relevance"], reverse=True)
        
        return timestamps
    
    def _calculate_confidence(self, chunks: List[Dict[str, Any]]) -> float:
        """
        Calculate confidence score based on chunk relevance
        
        Args:
            chunks: List of relevant chunks
            
        Returns:
            Confidence score (0.0 to 1.0)
        """
        if not chunks:
            return 0.0
        
        # Average relevance score of top chunks
        relevance_scores = [chunk.get("relevance_score", 0.0) for chunk in chunks]
        avg_relevance = sum(relevance_scores) / len(relevance_scores)
        
        # Boost confidence if we have multiple relevant chunks
        chunk_count_factor = min(len(chunks) / 3.0, 1.0)  # Max boost at 3+ chunks
        
        # Final confidence combines relevance and chunk count
        confidence = (avg_relevance * 0.7) + (chunk_count_factor * 0.3)
        
        return min(confidence, 1.0)
    
    def _format_timestamp(self, seconds: float) -> str:
        """
        Format timestamp for display
        
        Args:
            seconds: Time in seconds
            
        Returns:
            Formatted timestamp (MM:SS or HH:MM:SS)
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = int(seconds % 60)
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"
    
    async def get_lecture_summary(self, video_id: str) -> Dict[str, Any]:
        """
        Generate a summary of the entire lecture
        
        Args:
            video_id: Video identifier
            
        Returns:
            Lecture summary with key points
        """
        try:
            # Get all chunks for the video
            all_chunks = await self.rag_pipeline.search_relevant_chunks(
                query="summary overview main points key topics", 
                video_id=video_id, 
                top_k=10
            )
            
            if not all_chunks:
                return {
                    "summary": "No content available for summary.",
                    "key_points": [],
                    "duration": 0.0
                }
            
            # Prepare context for summary
            context = self._prepare_context(all_chunks)
            
            # Generate summary using Gemini
            summary_prompt = f"""
Based on the following lecture transcript segments, provide a comprehensive summary:

LECTURE CONTENT:
{context}

Please provide:
1. A concise overall summary (2-3 paragraphs)
2. Key points covered in the lecture
3. Main topics discussed

Format your response as a clear, structured summary that would help students review the material.
"""
            
            summary_response = await asyncio.get_event_loop().run_in_executor(
                None, 
                self.model.generate_content, 
                summary_prompt
            )
            
            # Calculate total duration
            total_duration = max([chunk["end_time"] for chunk in all_chunks]) if all_chunks else 0.0
            
            return {
                "summary": summary_response.text,
                "key_points": self._extract_key_points(all_chunks),
                "duration": total_duration
            }
            
        except Exception as e:
            logger.error(f"Summary generation error: {e}")
            return {
                "summary": "Unable to generate summary at this time.",
                "key_points": [],
                "duration": 0.0
            }
    
    def _extract_key_points(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extract key points from chunks
        
        Args:
            chunks: List of chunks
            
        Returns:
            List of key points with timestamps
        """
        key_points = []
        
        for chunk in chunks[:5]:  # Top 5 most relevant chunks
            point = {
                "text": chunk["text"][:200] + "..." if len(chunk["text"]) > 200 else chunk["text"],
                "timestamp": chunk["start_time"],
                "formatted_time": self._format_timestamp(chunk["start_time"])
            }
            key_points.append(point)
        
        return key_points 