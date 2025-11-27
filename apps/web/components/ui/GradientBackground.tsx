'use client'

import { useEffect, useState } from 'react'

/**
 * GradientBackground - Creates the magical midnight indigo atmosphere
 * Includes animated floating particles for visual interest
 */
export function GradientBackground({ children }: { children: React.ReactNode }) {
  const [particles, setParticles] = useState<Array<{ id: number; left: number; delay: number; size: number }>>([])

  useEffect(() => {
    // Generate random particles on mount (client-side only)
    const newParticles = Array.from({ length: 50 }, (_, i) => ({
      id: i,
      left: Math.random() * 100,
      delay: Math.random() * 15,
      size: Math.random() * 2 + 1,
    }))
    setParticles(newParticles)
  }, [])

  return (
    <div className="relative min-h-screen overflow-hidden">
      {/* Base gradient background */}
      <div
        className="fixed inset-0 -z-20"
        style={{
          background: `
            radial-gradient(ellipse 80% 50% at 50% -20%, rgba(124, 58, 237, 0.3), transparent),
            radial-gradient(ellipse 60% 40% at 80% 100%, rgba(236, 72, 153, 0.15), transparent),
            radial-gradient(ellipse 60% 40% at 20% 100%, rgba(124, 58, 237, 0.15), transparent),
            linear-gradient(180deg, #0a0a1a 0%, #1e1b4b 50%, #0a0a1a 100%)
          `,
        }}
      />

      {/* Soft glow behind hero area */}
      <div
        className="fixed top-0 left-1/2 -translate-x-1/2 w-[800px] h-[600px] -z-10 pointer-events-none"
        style={{
          background: 'radial-gradient(ellipse at center, rgba(139, 92, 246, 0.15) 0%, transparent 70%)',
          filter: 'blur(60px)',
        }}
      />

      {/* Animated particles */}
      <div className="particles">
        {particles.map((particle) => (
          <div
            key={particle.id}
            className="particle"
            style={{
              left: `${particle.left}%`,
              bottom: '-10px',
              width: `${particle.size}px`,
              height: `${particle.size}px`,
              animationDelay: `${particle.delay}s`,
              opacity: 0.3 + Math.random() * 0.4,
            }}
          />
        ))}
      </div>

      {/* Content */}
      <div className="relative z-10">
        {children}
      </div>
    </div>
  )
}

export default GradientBackground
