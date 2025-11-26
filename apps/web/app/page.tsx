import Link from 'next/link'

export default function Home() {
  return (
    <main style={{
      minHeight: '100vh',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '2rem',
      textAlign: 'center',
    }}>
      <div style={{
        maxWidth: '800px',
        backgroundColor: 'white',
        padding: '3rem',
        borderRadius: '12px',
        boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
      }}>
        {/* Logo/Brand */}
        <div style={{
          fontSize: '3rem',
          fontWeight: 'bold',
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          marginBottom: '1rem',
        }}>
          AuthorFlow
        </div>

        {/* Tagline */}
        <h1 style={{
          fontSize: '2rem',
          fontWeight: '600',
          color: '#1a202c',
          marginBottom: '1rem',
        }}>
          Audiobook Engine
        </h1>

        <p style={{
          fontSize: '1.25rem',
          color: '#4a5568',
          marginBottom: '2rem',
          lineHeight: '1.6',
        }}>
          Turn your manuscript into a studio-ready audiobook in one workflow.
        </p>

        {/* Features */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: '1.5rem',
          marginBottom: '2.5rem',
          textAlign: 'left',
        }}>
          <FeatureCard
            icon="🎙️"
            title="Multi-Voice Support"
            description="Single narrator or dual-voice character dialogues"
          />
          <FeatureCard
            icon="⚡"
            title="Fast Processing"
            description="Parallel chunk processing for quick turnaround"
          />
          <FeatureCard
            icon="🎯"
            title="Studio Quality"
            description="Professional-grade TTS with multiple providers"
          />
        </div>

        {/* CTA Buttons */}
        <div style={{
          display: 'flex',
          gap: '1rem',
          justifyContent: 'center',
          flexWrap: 'wrap',
        }}>
          <Link
            href="/app"
            style={{
              padding: '0.75rem 2rem',
              fontSize: '1.125rem',
              fontWeight: '600',
              color: 'white',
              backgroundColor: '#667eea',
              border: 'none',
              borderRadius: '8px',
              textDecoration: 'none',
              cursor: 'pointer',
              transition: 'background-color 0.2s',
            }}
            onMouseOver={(e) => e.currentTarget.style.backgroundColor = '#5a67d8'}
            onMouseOut={(e) => e.currentTarget.style.backgroundColor = '#667eea'}
          >
            Launch App →
          </Link>

          <button
            style={{
              padding: '0.75rem 2rem',
              fontSize: '1.125rem',
              fontWeight: '600',
              color: '#667eea',
              backgroundColor: 'white',
              border: '2px solid #667eea',
              borderRadius: '8px',
              cursor: 'pointer',
              transition: 'all 0.2s',
            }}
            onMouseOver={(e) => {
              e.currentTarget.style.backgroundColor = '#f7fafc'
            }}
            onMouseOut={(e) => {
              e.currentTarget.style.backgroundColor = 'white'
            }}
          >
            Join Waitlist
          </button>
        </div>

        {/* Footer Note */}
        <p style={{
          marginTop: '2rem',
          fontSize: '0.875rem',
          color: '#718096',
        }}>
          Powered by OpenAI, ElevenLabs, and Inworld TTS
        </p>
      </div>
    </main>
  )
}

// Feature Card Component
function FeatureCard({
  icon,
  title,
  description,
}: {
  icon: string
  title: string
  description: string
}) {
  return (
    <div style={{
      padding: '1rem',
      backgroundColor: '#f7fafc',
      borderRadius: '8px',
    }}>
      <div style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>{icon}</div>
      <h3 style={{
        fontSize: '1rem',
        fontWeight: '600',
        color: '#2d3748',
        marginBottom: '0.25rem',
      }}>
        {title}
      </h3>
      <p style={{
        fontSize: '0.875rem',
        color: '#718096',
        lineHeight: '1.5',
      }}>
        {description}
      </p>
    </div>
  )
}
