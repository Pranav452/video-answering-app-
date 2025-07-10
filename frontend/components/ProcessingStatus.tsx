'use client'

import { useEffect, useState } from 'react'
import { VideoStatus } from '@/types/video'
import { getVideoStatus } from '@/lib/api'
import { Loader2, CheckCircle, XCircle } from 'lucide-react'

interface ProcessingStatusProps {
  videoId: string
  status: VideoStatus
  onStatusUpdate: (status: VideoStatus) => void
}

export default function ProcessingStatus({
  videoId,
  status,
  onStatusUpdate
}: ProcessingStatusProps) {
  const [currentStatus, setCurrentStatus] = useState<VideoStatus>(status)

  useEffect(() => {
    let interval: NodeJS.Timeout | null = null

    const checkStatus = async () => {
      try {
        const updatedStatus = await getVideoStatus(videoId)
        setCurrentStatus(updatedStatus)
        onStatusUpdate(updatedStatus)

        // Stop polling if completed or failed
        if (updatedStatus.status === 'completed' || updatedStatus.status === 'failed') {
          if (interval) {
            clearInterval(interval)
          }
        }
      } catch (error) {
        console.error('Failed to check video status:', error)
      }
    }

    // Start polling every 2 seconds
    interval = setInterval(checkStatus, 2000)

    // Cleanup on unmount
    return () => {
      if (interval) {
        clearInterval(interval)
      }
    }
  }, [videoId, onStatusUpdate])

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'text-green-600'
      case 'failed':
        return 'text-red-600'
      default:
        return 'text-blue-600'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-6 w-6 text-green-600" />
      case 'failed':
        return <XCircle className="h-6 w-6 text-red-600" />
      default:
        return <Loader2 className="h-6 w-6 text-blue-600 animate-spin" />
    }
  }

  const getStatusText = (status: string) => {
    switch (status) {
      case 'uploaded':
        return 'Video uploaded successfully'
      case 'extracting_audio':
        return 'Extracting audio from video'
      case 'transcribing':
        return 'Generating transcript with AI'
      case 'processing_rag':
        return 'Processing content for search'
      case 'completed':
        return 'Processing completed! You can now chat with your lecture.'
      case 'failed':
        return 'Processing failed. Please try uploading again.'
      default:
        return 'Processing...'
    }
  }

  return (
    <div className="max-w-2xl mx-auto">
      <div className="bg-card border rounded-lg p-6">
        <div className="text-center space-y-4">
          {/* Status Icon */}
          <div className="flex justify-center">
            {getStatusIcon(currentStatus.status)}
          </div>

          {/* Status Title */}
          <h2 className="text-2xl font-bold">Processing Your Lecture</h2>

          {/* Status Message */}
          <p className={`text-lg ${getStatusColor(currentStatus.status)}`}>
            {getStatusText(currentStatus.status)}
          </p>

          {/* Progress Bar */}
          {currentStatus.status !== 'completed' && currentStatus.status !== 'failed' && (
            <div className="w-full bg-secondary rounded-full h-3">
              <div
                className="bg-primary h-3 rounded-full transition-all duration-500"
                style={{ width: `${currentStatus.progress}%` }}
              />
            </div>
          )}

          {/* Progress Percentage */}
          {currentStatus.status !== 'completed' && currentStatus.status !== 'failed' && (
            <p className="text-sm text-muted-foreground">
              {Math.round(currentStatus.progress)}% complete
            </p>
          )}

          {/* Detailed Status Message */}
          {currentStatus.message && (
            <p className="text-sm text-muted-foreground">
              {currentStatus.message}
            </p>
          )}

          {/* Processing Steps */}
          <div className="mt-8 space-y-3">
            <h3 className="text-lg font-semibold">Processing Steps:</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Step 1: Audio Extraction */}
              <div className={`flex items-center space-x-3 p-3 rounded-lg border ${
                ['extracting_audio', 'transcribing', 'processing_rag', 'completed'].includes(currentStatus.status)
                  ? 'bg-green-50 border-green-200 text-green-700'
                  : 'bg-muted text-muted-foreground'
              }`}>
                <div className={`w-2 h-2 rounded-full ${
                  ['extracting_audio', 'transcribing', 'processing_rag', 'completed'].includes(currentStatus.status)
                    ? 'bg-green-600'
                    : 'bg-muted-foreground'
                }`} />
                <span className="text-sm">Audio Extraction</span>
              </div>

              {/* Step 2: Transcription */}
              <div className={`flex items-center space-x-3 p-3 rounded-lg border ${
                ['transcribing', 'processing_rag', 'completed'].includes(currentStatus.status)
                  ? 'bg-green-50 border-green-200 text-green-700'
                  : 'bg-muted text-muted-foreground'
              }`}>
                <div className={`w-2 h-2 rounded-full ${
                  ['transcribing', 'processing_rag', 'completed'].includes(currentStatus.status)
                    ? 'bg-green-600'
                    : 'bg-muted-foreground'
                }`} />
                <span className="text-sm">AI Transcription</span>
              </div>

              {/* Step 3: RAG Processing */}
              <div className={`flex items-center space-x-3 p-3 rounded-lg border ${
                ['processing_rag', 'completed'].includes(currentStatus.status)
                  ? 'bg-green-50 border-green-200 text-green-700'
                  : 'bg-muted text-muted-foreground'
              }`}>
                <div className={`w-2 h-2 rounded-full ${
                  ['processing_rag', 'completed'].includes(currentStatus.status)
                    ? 'bg-green-600'
                    : 'bg-muted-foreground'
                }`} />
                <span className="text-sm">Content Analysis</span>
              </div>

              {/* Step 4: Completion */}
              <div className={`flex items-center space-x-3 p-3 rounded-lg border ${
                currentStatus.status === 'completed'
                  ? 'bg-green-50 border-green-200 text-green-700'
                  : 'bg-muted text-muted-foreground'
              }`}>
                <div className={`w-2 h-2 rounded-full ${
                  currentStatus.status === 'completed'
                    ? 'bg-green-600'
                    : 'bg-muted-foreground'
                }`} />
                <span className="text-sm">Ready to Chat</span>
              </div>
            </div>
          </div>

          {/* Estimated Time */}
          {currentStatus.status !== 'completed' && currentStatus.status !== 'failed' && (
            <div className="mt-6 p-4 bg-muted rounded-lg">
              <p className="text-sm text-muted-foreground">
                ⏱️ Processing typically takes 2-5 minutes for a 1-hour lecture
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
} 