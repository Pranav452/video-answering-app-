'use client'

import { useState, useRef, useEffect } from 'react'
import { Send, User, Bot, Clock, AlertCircle } from 'lucide-react'
import { sendChatMessage, formatTimestamp, handleApiError } from '@/lib/api'
import { ChatMessage } from '@/types/video'

interface ChatInterfaceProps {
  videoId: string
  onTimestampClick: (timestamp: number) => void
}

export default function ChatInterface({ videoId, onTimestampClick }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSendMessage = async () => {
    if (!input.trim() || isLoading) return

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      message: input,
      timestamp: new Date(),
      isUser: true,
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setIsLoading(true)
    setError(null)

    try {
      const response = await sendChatMessage(input, videoId)
      
      const botMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        message: input,
        response: response.response,
        timestamps: response.timestamps,
        confidence: response.confidence,
        timestamp: new Date(),
        isUser: false,
      }

      setMessages(prev => [...prev, botMessage])
    } catch (error) {
      setError(handleApiError(error))
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  const handleTimestampClickInternal = (timestamp: number) => {
    onTimestampClick(timestamp)
  }

  return (
    <div className="flex flex-col h-[600px] bg-card border rounded-lg">
      {/* Chat Header */}
      <div className="p-4 border-b bg-muted/50">
        <h3 className="font-semibold flex items-center space-x-2">
          <Bot className="h-5 w-5" />
          <span>Chat with Lecture</span>
        </h3>
        <p className="text-sm text-muted-foreground mt-1">
          Ask questions about the lecture content
        </p>
      </div>

      {/* Messages Container */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center text-muted-foreground py-8">
            <Bot className="h-12 w-12 mx-auto mb-4 opacity-50" />
            <p>Start a conversation about your lecture!</p>
            <p className="text-sm mt-2">Try asking things like:</p>
            <ul className="text-sm mt-2 space-y-1">
              <li>"What was discussed about machine learning?"</li>
              <li>"Summarize the key points"</li>
              <li>"What examples were given?"</li>
            </ul>
          </div>
        )}

        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.isUser ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[80%] rounded-lg p-3 ${
                message.isUser
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-secondary text-secondary-foreground'
              }`}
            >
              {/* Message Header */}
              <div className="flex items-center space-x-2 mb-2">
                {message.isUser ? (
                  <User className="h-4 w-4" />
                ) : (
                  <Bot className="h-4 w-4" />
                )}
                <span className="text-xs opacity-70">
                  {message.timestamp.toLocaleTimeString()}
                </span>
              </div>

              {/* User Message */}
              {message.isUser && (
                <p className="text-sm">{message.message}</p>
              )}

              {/* Bot Response */}
              {!message.isUser && message.response && (
                <div className="space-y-3">
                  <p className="text-sm whitespace-pre-wrap">{message.response}</p>

                  {/* Timestamps */}
                  {message.timestamps && message.timestamps.length > 0 && (
                    <div className="space-y-2">
                      <div className="flex items-center space-x-2">
                        <Clock className="h-4 w-4" />
                        <span className="text-xs font-medium">Relevant timestamps:</span>
                      </div>
                      <div className="flex flex-wrap gap-2">
                        {message.timestamps.slice(0, 3).map((timestamp, index) => (
                          <button
                            key={index}
                            onClick={() => handleTimestampClickInternal(timestamp.start)}
                            className="px-2 py-1 bg-accent text-accent-foreground rounded text-xs hover:bg-accent/80 transition-colors"
                          >
                            {formatTimestamp(timestamp.start)}
                          </button>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Confidence Score */}
                  {message.confidence !== undefined && (
                    <div className="flex items-center space-x-2">
                      <div className="flex-1 bg-muted rounded-full h-1">
                        <div
                          className="bg-primary h-1 rounded-full"
                          style={{ width: `${message.confidence * 100}%` }}
                        />
                      </div>
                      <span className="text-xs opacity-70">
                        {Math.round(message.confidence * 100)}% confidence
                      </span>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        ))}

        {/* Loading Message */}
        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-secondary text-secondary-foreground rounded-lg p-3">
              <div className="flex items-center space-x-2">
                <Bot className="h-4 w-4" />
                <span className="text-xs opacity-70">Thinking...</span>
              </div>
              <div className="flex space-x-1 mt-2">
                <div className="w-2 h-2 bg-current rounded-full animate-bounce"></div>
                <div className="w-2 h-2 bg-current rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                <div className="w-2 h-2 bg-current rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
              </div>
            </div>
          </div>
        )}

        {/* Error Message */}
        {error && (
          <div className="bg-destructive/10 border border-destructive/20 rounded-lg p-3">
            <div className="flex items-center space-x-2">
              <AlertCircle className="h-4 w-4 text-destructive" />
              <p className="text-sm text-destructive">{error}</p>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="p-4 border-t bg-muted/50">
        <div className="flex space-x-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask a question about the lecture..."
            className="flex-1 px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary bg-background"
            disabled={isLoading}
          />
          <button
            onClick={handleSendMessage}
            disabled={!input.trim() || isLoading}
            className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <Send className="h-4 w-4" />
          </button>
        </div>
        <p className="text-xs text-muted-foreground mt-2">
          Press Enter to send, Shift+Enter for new line
        </p>
      </div>
    </div>
  )
} 