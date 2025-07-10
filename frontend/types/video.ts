export interface VideoStatus {
  video_id: string
  status: 'uploaded' | 'extracting_audio' | 'transcribing' | 'processing_rag' | 'completed' | 'failed'
  progress: number
  message: string
}

export interface ChatMessage {
  id: string
  message: string
  response?: string
  timestamps?: Array<{
    start: number
    end: number
    relevance: number
  }>
  confidence?: number
  timestamp: Date
  isUser: boolean
}

export interface VideoInfo {
  video_id: string
  filename: string
  duration: number
  status: VideoStatus['status']
  uploaded_at: Date
}

export interface ChatResponse {
  response: string
  timestamps: Array<{
    start: number
    end: number
    relevance: number
  }>
  confidence: number
}

export interface UploadProgress {
  loaded: number
  total: number
  percentage: number
} 