'use client'

import { useState, useEffect } from 'react'
import VideoUpload from '@/components/VideoUpload'
import VideoPlayer from '@/components/VideoPlayer'
import ChatInterface from '@/components/ChatInterface'
import ProcessingStatus from '@/components/ProcessingStatus'
import { VideoStatus } from '@/types/video'

export default function Home() {
  const [currentVideo, setCurrentVideo] = useState<string | null>(null)
  const [videoStatus, setVideoStatus] = useState<VideoStatus | null>(null)
  const [videoUrl, setVideoUrl] = useState<string | null>(null)
  const [currentTime, setCurrentTime] = useState<number>(0)

  // Handle video upload completion
  const handleUploadComplete = (videoId: string) => {
    setCurrentVideo(videoId)
    setVideoStatus({ video_id: videoId, status: 'uploaded', progress: 0, message: 'Processing started...' })
  }

  // Handle processing completion
  const handleProcessingComplete = (status: VideoStatus) => {
    setVideoStatus(status)
    if (status.status === 'completed') {
      // Set video URL for playback (you might need to adjust this based on your backend)
      setVideoUrl(`/api/video/${currentVideo}`)
    }
  }

  // Handle timestamp seeking from chat
  const handleTimestampClick = (timestamp: number) => {
    setCurrentTime(timestamp)
  }

  return (
    <div className="max-w-7xl mx-auto space-y-8">
      {/* Video Upload Section */}
      {!currentVideo && (
        <div className="text-center">
          <h2 className="text-3xl font-bold mb-4">Upload Your Lecture Video</h2>
          <p className="text-muted-foreground mb-8">
            Upload a lecture video to start chatting with the content
          </p>
          <VideoUpload onUploadComplete={handleUploadComplete} />
        </div>
      )}

      {/* Processing Status */}
      {currentVideo && videoStatus && videoStatus.status !== 'completed' && (
        <ProcessingStatus
          status={videoStatus}
          onStatusUpdate={handleProcessingComplete}
          videoId={currentVideo}
        />
      )}

      {/* Main Interface - Video Player and Chat */}
      {currentVideo && videoStatus && videoStatus.status === 'completed' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Video Player Section */}
          <div className="space-y-4">
            <h2 className="text-2xl font-bold">Lecture Video</h2>
            <VideoPlayer
              videoUrl={videoUrl}
              currentTime={currentTime}
              onTimeUpdate={setCurrentTime}
            />
          </div>

          {/* Chat Interface Section */}
          <div className="space-y-4">
            <h2 className="text-2xl font-bold">Chat with Lecture</h2>
            <ChatInterface
              videoId={currentVideo}
              onTimestampClick={handleTimestampClick}
            />
          </div>
        </div>
      )}

      {/* Help Section */}
      <div className="bg-card p-6 rounded-lg border">
        <h3 className="text-xl font-semibold mb-4">How to use Lecture Intelligence</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <h4 className="font-medium mb-2">1. Upload Video</h4>
            <p className="text-sm text-muted-foreground">
              Upload your lecture video (MP4, AVI, MOV, MKV, WebM supported)
            </p>
          </div>
          <div>
            <h4 className="font-medium mb-2">2. Processing</h4>
            <p className="text-sm text-muted-foreground">
              Wait for the AI to transcribe and analyze your lecture content
            </p>
          </div>
          <div>
            <h4 className="font-medium mb-2">3. Ask Questions</h4>
            <p className="text-sm text-muted-foreground">
              Chat with your lecture content and get timestamp-based answers
            </p>
          </div>
          <div>
            <h4 className="font-medium mb-2">4. Navigate</h4>
            <p className="text-sm text-muted-foreground">
              Click on timestamps to jump to specific moments in the video
            </p>
          </div>
        </div>
      </div>

      {/* Sample Questions */}
      {currentVideo && videoStatus && videoStatus.status === 'completed' && (
        <div className="bg-muted p-6 rounded-lg">
          <h3 className="text-xl font-semibold mb-4">Sample Questions to Try</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
            <div className="text-sm text-muted-foreground">
              "What did the professor say about machine learning?"
            </div>
            <div className="text-sm text-muted-foreground">
              "Explain the concept discussed around minute 45"
            </div>
            <div className="text-sm text-muted-foreground">
              "Summarize the key points from the first hour"
            </div>
            <div className="text-sm text-muted-foreground">
              "What examples were given for neural networks?"
            </div>
          </div>
        </div>
      )}
    </div>
  )
} 