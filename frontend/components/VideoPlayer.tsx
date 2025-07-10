'use client'

import { useEffect, useRef, useState } from 'react'
import ReactPlayer from 'react-player'
import { Play, Pause, Volume2, VolumeX, SkipBack, SkipForward } from 'lucide-react'

interface VideoPlayerProps {
  videoUrl: string | null
  currentTime: number
  onTimeUpdate: (time: number) => void
}

export default function VideoPlayer({ videoUrl, currentTime, onTimeUpdate }: VideoPlayerProps) {
  const playerRef = useRef<ReactPlayer>(null)
  const [playing, setPlaying] = useState(false)
  const [volume, setVolume] = useState(0.8)
  const [muted, setMuted] = useState(false)
  const [duration, setDuration] = useState(0)
  const [played, setPlayed] = useState(0)
  const [seeking, setSeeking] = useState(false)

  // Seek to specific time when currentTime prop changes
  useEffect(() => {
    if (playerRef.current && currentTime !== undefined) {
      playerRef.current.seekTo(currentTime)
    }
  }, [currentTime])

  const handlePlayPause = () => {
    setPlaying(!playing)
  }

  const handleProgress = (state: { played: number; playedSeconds: number }) => {
    if (!seeking) {
      setPlayed(state.played)
      onTimeUpdate(state.playedSeconds)
    }
  }

  const handleSeekMouseDown = () => {
    setSeeking(true)
  }

  const handleSeekChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = parseFloat(e.target.value)
    setPlayed(value)
  }

  const handleSeekMouseUp = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSeeking(false)
    const value = parseFloat(e.target.value)
    if (playerRef.current) {
      playerRef.current.seekTo(value)
    }
  }

  const handleVolumeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = parseFloat(e.target.value)
    setVolume(value)
    setMuted(value === 0)
  }

  const handleMute = () => {
    setMuted(!muted)
  }

  const handleSkipBack = () => {
    if (playerRef.current) {
      const currentTime = playerRef.current.getCurrentTime()
      playerRef.current.seekTo(Math.max(0, currentTime - 10))
    }
  }

  const handleSkipForward = () => {
    if (playerRef.current) {
      const currentTime = playerRef.current.getCurrentTime()
      playerRef.current.seekTo(Math.min(duration, currentTime + 10))
    }
  }

  const formatTime = (seconds: number) => {
    const date = new Date(seconds * 1000)
    const hh = date.getUTCHours()
    const mm = date.getUTCMinutes()
    const ss = date.getUTCSeconds()
    
    if (hh) {
      return `${hh}:${mm.toString().padStart(2, '0')}:${ss.toString().padStart(2, '0')}`
    } else {
      return `${mm}:${ss.toString().padStart(2, '0')}`
    }
  }

  if (!videoUrl) {
    return (
      <div className="bg-card border rounded-lg p-8 text-center">
        <p className="text-muted-foreground">No video available</p>
      </div>
    )
  }

  return (
    <div className="bg-card border rounded-lg overflow-hidden">
      {/* Video Player */}
      <div className="relative aspect-video bg-black">
        <ReactPlayer
          ref={playerRef}
          url={videoUrl}
          width="100%"
          height="100%"
          playing={playing}
          volume={muted ? 0 : volume}
          onProgress={handleProgress}
          onDuration={setDuration}
          onReady={() => console.log('Video ready')}
          onError={(error) => console.error('Video error:', error)}
          controls={false}
          className="react-player"
        />
        
        {/* Custom Play/Pause Overlay */}
        <div 
          className="absolute inset-0 flex items-center justify-center bg-black bg-opacity-0 hover:bg-opacity-30 transition-all cursor-pointer"
          onClick={handlePlayPause}
        >
          {!playing && (
            <Play className="h-16 w-16 text-white opacity-80" />
          )}
        </div>
      </div>

      {/* Custom Controls */}
      <div className="p-4 bg-card space-y-3">
        {/* Progress Bar */}
        <div className="flex items-center space-x-3">
          <span className="text-sm text-muted-foreground min-w-[3rem]">
            {formatTime(played * duration)}
          </span>
          <input
            type="range"
            min={0}
            max={1}
            step={0.001}
            value={played}
            onChange={handleSeekChange}
            onMouseDown={handleSeekMouseDown}
            onMouseUp={handleSeekMouseUp}
            className="flex-1 h-2 bg-secondary rounded-lg cursor-pointer"
          />
          <span className="text-sm text-muted-foreground min-w-[3rem]">
            {formatTime(duration)}
          </span>
        </div>

        {/* Control Buttons */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            {/* Skip Back */}
            <button
              onClick={handleSkipBack}
              className="p-2 rounded-full hover:bg-accent transition-colors"
            >
              <SkipBack className="h-5 w-5" />
            </button>

            {/* Play/Pause */}
            <button
              onClick={handlePlayPause}
              className="p-2 rounded-full hover:bg-accent transition-colors"
            >
              {playing ? (
                <Pause className="h-5 w-5" />
              ) : (
                <Play className="h-5 w-5" />
              )}
            </button>

            {/* Skip Forward */}
            <button
              onClick={handleSkipForward}
              className="p-2 rounded-full hover:bg-accent transition-colors"
            >
              <SkipForward className="h-5 w-5" />
            </button>
          </div>

          {/* Volume Control */}
          <div className="flex items-center space-x-2">
            <button
              onClick={handleMute}
              className="p-2 rounded-full hover:bg-accent transition-colors"
            >
              {muted ? (
                <VolumeX className="h-5 w-5" />
              ) : (
                <Volume2 className="h-5 w-5" />
              )}
            </button>
            <input
              type="range"
              min={0}
              max={1}
              step={0.01}
              value={muted ? 0 : volume}
              onChange={handleVolumeChange}
              className="w-20 h-2 bg-secondary rounded-lg cursor-pointer"
            />
          </div>
        </div>
      </div>
    </div>
  )
} 