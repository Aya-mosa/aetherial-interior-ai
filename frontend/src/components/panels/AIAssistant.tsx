'use client'
import { useState, useRef, useEffect } from 'react'
import { useStore } from '@/store/useStore'
import { api } from '@/lib/api'

// ── Site context for the AI (bilingual) ───────────────────────────────────────
const SITE_CONTEXT = `
You are the AI Interior Architect of "Aetherial Interior AI" — an intelligent interior design platform.
You are a bilingual assistant: respond in the same language the user writes in (Arabic or English).
If the user writes in Arabic, reply fully in Arabic. If in English, reply in English.

ABOUT THE PLATFORM (for answering user questions):
- Aetherial is an AI-powered interior design tool built for DEPI (Digital Egypt Pioneers Initiative)
- Users upload a photo of their room, choose a style and furniture, then the AI generates a redesigned version
- The platform uses a 6-agent AI pipeline: preprocessing → spatial planning → vision analysis → validation → prompt engineering → image generation
- Supported room types: Bedroom, Living Room, Kitchen, Bathroom, Office, Dining Room
- Supported styles: Modern, Minimalist, Bohemian, Industrial, Scandinavian, Japandi, Classic, Farmhouse
- After generation, users can: compare before/after, view the floor plan, drag furniture, re-render, and download the result
- The AI Architect chatbot (that's you) can help move furniture, suggest design changes, and answer design questions

YOUR ROLE:
1. Answer questions about the platform, how it works, pricing (free to use), features
2. Help with interior design advice in Arabic or English
3. Process furniture movement requests and return layout_changes
4. Be friendly, professional, and knowledgeable about interior design

IMPORTANT: Always reply in the SAME LANGUAGE as the user's message.
`

const QUICK_COMMANDS_EN = [
  'Move the sofa near the window',
  'Add warm lighting',
  'Make the room more minimal',
  'How does this platform work?',
  'What styles are available?',
]

const QUICK_COMMANDS_AR = [
  'حرّك الأريكة قرب النافذة',
  'أضف إضاءة دافئة',
  'اجعل الغرفة أكثر بساطة',
  'كيف يعمل هذا الموقع؟',
  'ما هي الأساليب المتاحة؟',
]

function detectArabic(text: string): boolean {
  return /[\u0600-\u06FF]/.test(text)
}

export function AIAssistant({ sessionId }: { sessionId: string }) {
  const { chatMessages, addChatMessage, toggleAssistant } = useStore()
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [isArabic, setIsArabic] = useState(false)
  const messagesRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (messagesRef.current) {
      messagesRef.current.scrollTop = messagesRef.current.scrollHeight
    }
  }, [chatMessages])

  // Detect language as user types
  useEffect(() => {
    if (input.length > 2) setIsArabic(detectArabic(input))
  }, [input])

  const QUICK_COMMANDS = isArabic ? QUICK_COMMANDS_AR : QUICK_COMMANDS_EN

  const send = async (msg: string) => {
    if (!msg.trim() || loading) return
    const userMsg = { role: 'user' as const, content: msg.trim(), timestamp: Date.now() }
    addChatMessage(userMsg)
    setInput('')
    setLoading(true)

    try {
      // Inject site context into the message so backend AI knows about the platform
      const enrichedMsg = `[CONTEXT: ${SITE_CONTEXT}]\n\nUser message: ${msg.trim()}`
      const res = await api.sendChat(sessionId, enrichedMsg)

      // Clean up the reply (remove any context echo)
      let reply = res.reply || ''
      if (reply.includes('[CONTEXT:')) {
        reply = reply.substring(reply.lastIndexOf(']') + 1).trim()
      }

      addChatMessage({
        role: 'assistant',
        content: reply || (isArabic ? 'حدث خطأ، يرجى المحاولة مرة أخرى.' : 'Something went wrong, please try again.'),
        timestamp: Date.now(),
      })
    } catch {
      addChatMessage({
        role: 'assistant',
        content: isArabic
          ? 'عذراً، حدث خطأ. يرجى المحاولة مجدداً.'
          : 'Sorry, I could not process that. Please try again.',
        timestamp: Date.now(),
      })
    } finally {
      setLoading(false)
    }
  }

  const placeholderText = isArabic
    ? 'اسألني أي شيء عن تصميمك…'
    : 'Ask anything about your design…'

  const emptyTitle = isArabic ? 'كيف يمكنني مساعدتك؟' : 'How can I help?'
  const emptySubtitle = isArabic
    ? 'اسألني عن التصميم، تحريك الأثاث، أو كيفية عمل الموقع.'
    : 'Ask me to adjust your design, move furniture, or explain how the platform works.'

  return (
    <div
      className="fixed right-6 bottom-24 z-40 w-80 glass-card flex flex-col"
      style={{
        height: '540px',
        animation: 'slideUp 0.4s cubic-bezier(0.16, 1, 0.3, 1) forwards',
        border: '1px solid rgba(201,168,76,0.15)',
      }}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-5 py-4 border-b border-white/06">
        <div className="flex items-center gap-3">
          <div className="w-7 h-7 rounded-full bg-gold/20 flex items-center justify-center text-gold text-sm">✦</div>
          <div>
            <p className="font-body text-sm font-medium text-marble">
              {isArabic ? 'المساعد الذكي' : 'AI Architect'}
            </p>
            <p className="font-body text-[10px] text-marble/30">
              {isArabic ? 'مستشار التصميم الداخلي · عربي / English' : 'Interior design advisor · عربي / English'}
            </p>
          </div>
        </div>
        <button
          onClick={toggleAssistant}
          className="text-marble/30 hover:text-marble/60 transition-colors text-lg"
        >
          ✕
        </button>
      </div>

      {/* Messages */}
      <div ref={messagesRef} className="flex-1 overflow-y-auto px-4 py-4 space-y-3">
        {chatMessages.length === 0 && (
          <div className="text-center pt-4">
            <p className="font-display text-xl text-marble/40 italic mb-2">{emptyTitle}</p>
            <p className="font-body text-xs text-marble/25">{emptySubtitle}</p>
          </div>
        )}
        {chatMessages.map((m, i) => (
          <div
            key={i}
            className={`text-xs font-body px-4 py-3 ${m.role === 'user' ? 'chat-msg-user text-right' : 'chat-msg-ai text-left'}`}
            dir={detectArabic(m.content) ? 'rtl' : 'ltr'}
          >
            <p className={m.role === 'user' ? 'text-marble/80' : 'text-marble/70'}>{m.content}</p>
            <p className="text-[10px] text-marble/20 mt-1.5">
              {new Date(m.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
            </p>
          </div>
        ))}
        {loading && (
          <div className="chat-msg-ai px-4 py-3">
            <div className="flex gap-1">
              {[0, 1, 2].map((d) => (
                <div
                  key={d}
                  className="w-1.5 h-1.5 rounded-full bg-gold/50"
                  style={{ animation: `pulse 1.2s ease ${d * 0.2}s infinite` }}
                />
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Quick commands */}
      {chatMessages.length === 0 && (
        <div className="px-4 pb-3 flex flex-wrap gap-2" dir={isArabic ? 'rtl' : 'ltr'}>
          {QUICK_COMMANDS.map((cmd) => (
            <button
              key={cmd}
              onClick={() => send(cmd)}
              className="text-[10px] font-body px-3 py-1.5 rounded-full border border-white/08 text-marble/40 hover:border-gold/30 hover:text-gold/60 transition-all duration-200"
            >
              {cmd}
            </button>
          ))}
        </div>
      )}

      {/* Input */}
      <div
        className="px-4 py-3 border-t border-white/06 flex gap-2"
        dir={isArabic ? 'rtl' : 'ltr'}
      >
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => { if (e.key === 'Enter') send(input) }}
          placeholder={placeholderText}
          dir={isArabic ? 'rtl' : 'ltr'}
          className="flex-1 rounded-xl px-4 py-2.5 text-xs font-body outline-none transition-colors focus:border-gold/30"
          style={{
            background: 'rgba(255,255,255,0.92)',
            border: '1px solid rgba(201,168,76,0.25)',
            color: '#1a1a1a',
          }}
        />
        <button
          onClick={() => send(input)}
          disabled={!input.trim() || loading}
          className="w-9 h-9 rounded-xl bg-gold/15 border border-gold/20 text-gold flex items-center justify-center text-sm hover:bg-gold/25 transition-all duration-200 disabled:opacity-30"
        >
          {isArabic ? '↑' : '↑'}
        </button>
      </div>
    </div>
  )
}
