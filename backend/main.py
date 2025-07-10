import os
import logging
from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
from typing import List, Dict, Optional
import aiofiles
import asyncio
from datetime import datetime
import uuid
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from services.video_processor import VideoProcessor
from services.rag_pipeline import RAGPipeline
from services.chat_service import ChatService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="Lecture Intelligence API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
video_processor = VideoProcessor()
rag_pipeline = RAGPipeline()
chat_service = ChatService(rag_pipeline)

# Data models
class ChatMessage(BaseModel):
    message: str
    video_id: str

class ChatResponse(BaseModel):
    response: str
    timestamps: List[Dict[str, float]]
    confidence: float

class VideoStatus(BaseModel):
    video_id: str
    status: str
    progress: float
    message: str

# In-memory storage for video processing status
video_status_store: Dict[str, VideoStatus] = {}

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Lecture Intelligence API is running"}

@app.post("/upload-video")
async def upload_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """
    Upload a lecture video and start processing pipeline
    """
    try:
        # Validate file
        if not file.filename.lower().endswith(('.mp4', '.avi', '.mov', '.mkv', '.webm')):
            raise HTTPException(status_code=400, detail="Invalid video format")
        
        if file.size > 2 * 1024 * 1024 * 1024:  # 2GB limit
            raise HTTPException(status_code=400, detail="File too large")
        
        # Generate unique video ID
        video_id = str(uuid.uuid4())
        
        # Create uploads directory
        os.makedirs("uploads", exist_ok=True)
        
        # Save uploaded file
        file_path = f"uploads/{video_id}_{file.filename}"
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        # Initialize status
        video_status_store[video_id] = VideoStatus(
            video_id=video_id,
            status="uploaded",
            progress=0.0,
            message="Video uploaded successfully"
        )
        
        # Start background processing
        background_tasks.add_task(process_video_pipeline, video_id, file_path)
        
        return {
            "video_id": video_id,
            "message": "Video uploaded successfully. Processing started.",
            "filename": file.filename
        }
        
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/video-status/{video_id}")
async def get_video_status(video_id: str):
    """
    Get processing status for a video
    """
    if video_id not in video_status_store:
        raise HTTPException(status_code=404, detail="Video not found")
    
    return video_status_store[video_id]

@app.post("/chat", response_model=ChatResponse)
async def chat_with_lecture(message: ChatMessage):
    """
    Chat with lecture content using RAG pipeline
    """
    try:
        # Check if video exists and is processed
        if message.video_id not in video_status_store:
            raise HTTPException(status_code=404, detail="Video not found")
        
        status = video_status_store[message.video_id]
        if status.status != "completed":
            raise HTTPException(
                status_code=400, 
                detail=f"Video is still processing. Status: {status.status}"
            )
        
        # Get response from chat service
        response = await chat_service.get_response(message.message, message.video_id)
        
        return response
        
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/video/{video_id}")
async def get_video(video_id: str):
    """
    Serve the uploaded video file
    """
    try:
        # Check if video exists
        if video_id not in video_status_store:
            raise HTTPException(status_code=404, detail="Video not found")
        
        # Find the video file
        video_files = []
        for filename in os.listdir("uploads"):
            if filename.startswith(video_id):
                video_files.append(filename)
        
        if not video_files:
            raise HTTPException(status_code=404, detail="Video file not found")
        
        video_file = video_files[0]
        file_path = f"uploads/{video_file}"
        
        # Return video file with proper headers
        return FileResponse(
            file_path,
            media_type="video/mp4",
            filename=video_file
        )
        
    except Exception as e:
        logger.error(f"Video serving error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/videos")
async def list_videos():
    """
    List all processed videos
    """
    try:
        videos = []
        for video_id, status in video_status_store.items():
            if status.status == "completed":
                videos.append({
                    "video_id": video_id,
                    "status": status.status,
                    "processed_at": datetime.now().isoformat()
                })
        return {"videos": videos}
    except Exception as e:
        logger.error(f"List videos error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def process_video_pipeline(video_id: str, file_path: str):
    """
    Background task to process video through the RAG pipeline
    """
    try:
        # Update status: extracting audio
        video_status_store[video_id].status = "extracting_audio"
        video_status_store[video_id].progress = 10.0
        video_status_store[video_id].message = "Extracting audio from video..."
        
        # Extract audio
        audio_path = await video_processor.extract_audio(file_path)
        
        # Update status: transcribing
        video_status_store[video_id].status = "transcribing"
        video_status_store[video_id].progress = 30.0
        video_status_store[video_id].message = "Generating transcript with timestamps..."
        
        # Generate transcript
        transcript = await video_processor.transcribe_audio(audio_path)
        
        # Update status: processing with RAG
        video_status_store[video_id].status = "processing_rag"
        video_status_store[video_id].progress = 70.0
        video_status_store[video_id].message = "Processing transcript with RAG pipeline..."
        
        # Process through RAG pipeline
        await rag_pipeline.process_transcript(transcript, video_id)
        
        # Update status: completed
        video_status_store[video_id].status = "completed"
        video_status_store[video_id].progress = 100.0
        video_status_store[video_id].message = "Processing completed successfully!"
        
        # Clean up temporary files
        os.remove(audio_path)
        
    except Exception as e:
        logger.error(f"Processing error for video {video_id}: {str(e)}")
        video_status_store[video_id].status = "failed"
        video_status_store[video_id].message = f"Processing failed: {str(e)}"

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 