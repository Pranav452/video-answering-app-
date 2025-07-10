import os
import logging
import asyncio
import ffmpeg
import whisper
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class VideoProcessor:
    """
    Handles video processing including audio extraction and transcription
    """
    
    def __init__(self):
        # Initialize Whisper model (using 'base' for good balance of speed/accuracy)
        # Available models: tiny, base, small, medium, large, large-v2, large-v3
        self.whisper_model = whisper.load_model("base")
        logger.info("Whisper model loaded successfully")
    
    async def extract_audio(self, video_path: str) -> str:
        """
        Extract audio from video file using FFmpeg
        
        Args:
            video_path: Path to the video file
            
        Returns:
            Path to the extracted audio file
        """
        try:
            # Generate audio output path
            audio_path = video_path.replace('.mp4', '.wav').replace('.avi', '.wav').replace('.mov', '.wav').replace('.mkv', '.wav').replace('.webm', '.wav')
            
            # Use FFmpeg to extract audio
            # Convert to WAV format for best compatibility with Whisper
            (
                ffmpeg
                .input(video_path)
                .output(audio_path, acodec='pcm_s16le', ar=16000)  # 16kHz sample rate for Whisper
                .overwrite_output()
                .run(quiet=True)
            )
            
            logger.info(f"Audio extracted successfully: {audio_path}")
            return audio_path
            
        except ffmpeg.Error as e:
            logger.error(f"FFmpeg error during audio extraction: {e}")
            raise Exception(f"Audio extraction failed: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during audio extraction: {e}")
            raise Exception(f"Audio extraction failed: {e}")
    
    async def transcribe_audio(self, audio_path: str) -> Dict[str, Any]:
        """
        Transcribe audio using OpenAI Whisper with timestamps
        
        Args:
            audio_path: Path to the audio file
            
        Returns:
            Dictionary containing transcript with timestamps and segments
        """
        try:
            # Run Whisper transcription in a separate thread to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, 
                self._transcribe_sync, 
                audio_path
            )
            
            # Process the result to extract segments with timestamps
            transcript_data = {
                "text": result["text"],
                "segments": [],
                "language": result["language"],
                "duration": 0.0
            }
            
            # Extract segments with timestamps
            for segment in result["segments"]:
                segment_data = {
                    "start": segment["start"],
                    "end": segment["end"],
                    "text": segment["text"].strip(),
                    "words": []
                }
                
                # Extract word-level timestamps if available
                if "words" in segment:
                    for word in segment["words"]:
                        word_data = {
                            "start": word["start"],
                            "end": word["end"],
                            "word": word["word"].strip()
                        }
                        segment_data["words"].append(word_data)
                
                transcript_data["segments"].append(segment_data)
            
            # Calculate total duration
            if transcript_data["segments"]:
                transcript_data["duration"] = transcript_data["segments"][-1]["end"]
            
            logger.info(f"Transcription completed: {len(transcript_data['segments'])} segments")
            return transcript_data
            
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            raise Exception(f"Transcription failed: {e}")
    
    def _transcribe_sync(self, audio_path: str) -> Dict[str, Any]:
        """
        Synchronous transcription method (runs in executor)
        """
        return self.whisper_model.transcribe(
            audio_path, 
            word_timestamps=True,  # Enable word-level timestamps
            language=None  # Auto-detect language
        )
    
    def format_timestamp(self, seconds: float) -> str:
        """
        Format timestamp in HH:MM:SS format
        
        Args:
            seconds: Time in seconds
            
        Returns:
            Formatted timestamp string
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = int(seconds % 60)
        
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    
    def get_segment_at_time(self, transcript: Dict[str, Any], target_time: float) -> Optional[Dict[str, Any]]:
        """
        Find the transcript segment at a specific time
        
        Args:
            transcript: Transcript data with segments
            target_time: Time in seconds
            
        Returns:
            Segment containing the target time
        """
        for segment in transcript["segments"]:
            if segment["start"] <= target_time <= segment["end"]:
                return segment
        
        return None 