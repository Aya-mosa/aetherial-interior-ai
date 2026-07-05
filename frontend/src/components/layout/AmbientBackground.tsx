'use client'
export function AmbientBackground() {
  return (
    <div className="fixed inset-0 z-0 overflow-hidden pointer-events-none">
      {/* Primary gold blob — top right */}
      <div
        className="ambient-blob w-[600px] h-[600px] opacity-[0.07]"
        style={{ background: 'radial-gradient(circle, #C9A84C, transparent)', top: '-200px', right: '-100px', animation: 'float 8s ease-in-out infinite' }}
      />
      {/* Sage blob — bottom left */}
      <div
        className="ambient-blob w-[500px] h-[500px] opacity-[0.05]"
        style={{ background: 'radial-gradient(circle, #8BA888, transparent)', bottom: '-150px', left: '-100px', animation: 'float 10s ease-in-out infinite reverse' }}
      />
      {/* Rust blob — center */}
      <div
        className="ambient-blob w-[400px] h-[400px] opacity-[0.04]"
        style={{ background: 'radial-gradient(circle, #B85C38, transparent)', top: '40%', left: '40%', animation: 'float 12s ease-in-out infinite 2s' }}
      />
      {/* Subtle grid lines */}
      <div
        className="absolute inset-0 opacity-[0.025]"
        style={{
          backgroundImage: `
            linear-gradient(rgba(201,168,76,0.3) 1px, transparent 1px),
            linear-gradient(90deg, rgba(201,168,76,0.3) 1px, transparent 1px)
          `,
          backgroundSize: '80px 80px',
        }}
      />
    </div>
  )
}
