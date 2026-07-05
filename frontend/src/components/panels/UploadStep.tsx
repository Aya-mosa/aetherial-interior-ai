'use client'
import { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { useStore } from '@/store/useStore'
import { ROOM_TYPES } from '@/lib/types'
import type { RoomType } from '@/lib/types'

const ROOM_ICONS: Record<RoomType, string> = {
  'Bedroom': '🛏',
  'Living Room': '🛋',
  'Office': '💼',
  'Gaming Room': '🎮',
  'Bathroom': '🚿',
  'Kitchen': '🍳',
}

export function UploadStep() {
  const { roomImageUrl, roomType, setRoomImage, setRoomType, setStep } = useStore()
  const [dragActive, setDragActive] = useState(false)

  const onDrop = useCallback((files: File[]) => {
    const file = files[0]
    if (!file) return
    const url = URL.createObjectURL(file)
    setRoomImage(file, url)
    setDragActive(false)
  }, [setRoomImage])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'image/*': ['.jpg', '.jpeg', '.png', '.webp'] },
    maxFiles: 1,
    onDragEnter: () => setDragActive(true),
    onDragLeave: () => setDragActive(false),
  })

  const canContinue = !!roomImageUrl

  return (
    <div className="min-h-screen pt-24 pb-16 px-6 flex flex-col items-center justify-center">
      <div className="max-w-2xl w-full">
        {/* Heading */}
        <div className="text-center mb-12" style={{ animation: 'slideUp 0.6s ease forwards' }}>
          <p className="text-gold/60 text-xs tracking-[0.3em] uppercase font-body mb-4">Step 1 of 3</p>
          <h1 className="font-display text-5xl md:text-6xl font-light text-marble leading-tight mb-4">
            Upload Your<br />
            <span className="text-gold-gradient italic">Empty Room</span>
          </h1>
          <p className="text-marble/40 font-body text-sm max-w-sm mx-auto leading-relaxed">
            Our AI analyzes the walls, windows, and spatial geometry to create an authentic design.
          </p>
        </div>

        {/* Dropzone */}
        <div
          {...getRootProps()}
          className={`upload-zone relative cursor-pointer transition-all duration-300 mb-8 ${isDragActive || dragActive ? 'active' : ''}`}
          style={{ animation: 'slideUp 0.6s ease 0.1s both' }}
        >
          <input {...getInputProps()} />

          {roomImageUrl ? (
            <div className="relative rounded-2xl overflow-hidden" style={{ minHeight: '320px' }}>
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={roomImageUrl} alt="Uploaded room" className="w-full object-cover" style={{ maxHeight: '400px' }} />
              <div className="absolute inset-0 bg-gradient-to-t from-obsidian/80 via-transparent to-transparent" />
              <div className="absolute bottom-4 left-4 right-4 flex items-center justify-between">
                <div className="glass-card px-3 py-1.5 text-xs text-marble/70 font-body">
                  ✓ Room image loaded
                </div>
                <div className="glass-card px-3 py-1.5 text-xs text-gold/70 font-body cursor-pointer hover:text-gold transition-colors">
                  Change →
                </div>
              </div>
            </div>
          ) : (
            <div className="py-20 text-center">
              <div className={`text-5xl mb-6 transition-transform duration-300 ${isDragActive ? 'scale-125' : ''}`}>
                {isDragActive ? '⬇' : '📷'}
              </div>
              <p className="text-marble/50 font-body text-sm mb-2">
                {isDragActive ? 'Drop your image here' : 'Drag & drop your room photo'}
              </p>
              <p className="text-marble/25 font-body text-xs">or click to browse — JPG, PNG, WebP</p>
            </div>
          )}
        </div>

        {/* Room type */}
        <div style={{ animation: 'slideUp 0.6s ease 0.2s both' }}>
          <p className="text-marble/40 text-xs tracking-[0.2em] uppercase font-body mb-4">Room Type</p>
          <div className="grid grid-cols-3 gap-3">
            {ROOM_TYPES.map((rt) => (
              <button
                key={rt}
                onClick={() => setRoomType(rt)}
                className={`furniture-card py-3 px-4 flex flex-col items-center gap-2 transition-all duration-200 ${roomType === rt ? 'selected' : ''}`}
              >
                <span className="text-2xl">{ROOM_ICONS[rt]}</span>
                <span className="text-xs font-body text-marble/60">{rt}</span>
              </button>
            ))}
          </div>
        </div>

        {/* CTA */}
        <div className="mt-10 flex justify-center" style={{ animation: 'slideUp 0.6s ease 0.3s both' }}>
          <button
            onClick={() => setStep('style')}
            disabled={!canContinue}
            className={`btn-gold px-10 py-4 rounded-2xl text-sm font-body tracking-wide transition-all duration-300 ${
              canContinue ? 'opacity-100' : 'opacity-30 cursor-not-allowed'
            }`}
          >
            Choose Your Style →
          </button>
        </div>
      </div>
    </div>
  )
}
