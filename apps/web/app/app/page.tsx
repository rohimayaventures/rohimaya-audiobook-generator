'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'

export default function AppDashboard() {
  const [apiHealth, setApiHealth] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Test connection to backend API
    const checkAPI = async () => {
      try {
        const apiUrl = process.env.NEXT_PUBLIC_ENGINE_API_URL || 'http://localhost:8000'
        const response = await fetch(`${apiUrl}/health`)
        const data = await response.json()
        setApiHealth(data)
      } catch (error) {
        setApiHealth({ status: 'error', message: 'Failed to connect to backend API' })
      } finally {
        setLoading(false)
      }
    }

    checkAPI()
  }, [])

  return (
    <main style={{
      minHeight: '100vh',
      backgroundColor: '#f5f5f5',
    }}>
      {/* Header */}
      <header style={{
        backgroundColor: 'white',
        borderBottom: '1px solid #e2e8f0',
        padding: '1rem 2rem',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <Link
            href="/"
            style={{
              fontSize: '1.5rem',
              fontWeight: 'bold',
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              textDecoration: 'none',
            }}
          >
            AuthorFlow
          </Link>
          <span style={{
            fontSize: '0.875rem',
            color: '#718096',
            padding: '0.25rem 0.75rem',
            backgroundColor: '#edf2f7',
            borderRadius: '12px',
          }}>
            Studio
          </span>
        </div>

        {/* API Health Badge */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem',
          fontSize: '0.875rem',
        }}>
          <span style={{ color: '#718096' }}>Backend API:</span>
          {loading ? (
            <span style={{ color: '#a0aec0' }}>Checking...</span>
          ) : (
            <span style={{
              color: apiHealth?.status === 'ok' ? '#48bb78' : '#f56565',
              fontWeight: '600',
            }}>
              {apiHealth?.status === 'ok' ? '● Connected' : '● Disconnected'}
            </span>
          )}
        </div>
      </header>

      {/* Main Content */}
      <div style={{
        maxWidth: '1200px',
        margin: '0 auto',
        padding: '2rem',
      }}>
        {/* Hero Section */}
        <div style={{
          backgroundColor: 'white',
          borderRadius: '12px',
          padding: '2rem',
          marginBottom: '2rem',
          boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
        }}>
          <h1 style={{
            fontSize: '2rem',
            fontWeight: '600',
            color: '#1a202c',
            marginBottom: '0.5rem',
          }}>
            AuthorFlow Studio
          </h1>
          <p style={{
            fontSize: '1.125rem',
            color: '#4a5568',
            marginBottom: '1.5rem',
          }}>
            Professional audiobook generation platform
          </p>

          {/* Coming Soon Badge */}
          <div style={{
            padding: '1.5rem',
            backgroundColor: '#f7fafc',
            borderRadius: '8px',
            border: '2px dashed #cbd5e0',
            textAlign: 'center',
          }}>
            <p style={{
              fontSize: '1.25rem',
              fontWeight: '600',
              color: '#2d3748',
              marginBottom: '0.5rem',
            }}>
              🚧 App Coming Soon
            </p>
            <p style={{
              fontSize: '1rem',
              color: '#718096',
            }}>
              This will be your dashboard for managing audiobook generation jobs
            </p>
          </div>
        </div>

        {/* Planned Features Grid */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
          gap: '1.5rem',
          marginBottom: '2rem',
        }}>
          <FeatureCard
            title="📤 Upload Manuscript"
            description="Upload TXT, DOCX, or PDF files, or paste text directly"
            status="planned"
          />
          <FeatureCard
            title="🎭 Choose Voice Mode"
            description="Single narrator or dual-voice character dialogue"
            status="planned"
          />
          <FeatureCard
            title="⚙️ Configure Settings"
            description="Select TTS provider, voices, and audio format"
            status="planned"
          />
          <FeatureCard
            title="📊 Track Progress"
            description="Real-time progress tracking for each job"
            status="planned"
          />
          <FeatureCard
            title="⬇️ Download Results"
            description="Download completed audiobooks in MP3, WAV, or M4B"
            status="planned"
          />
          <FeatureCard
            title="🔄 Regenerate Chapters"
            description="Re-generate specific chapters with different settings"
            status="planned"
          />
        </div>

        {/* API Test Panel */}
        <div style={{
          backgroundColor: 'white',
          borderRadius: '12px',
          padding: '2rem',
          boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
        }}>
          <h2 style={{
            fontSize: '1.5rem',
            fontWeight: '600',
            color: '#1a202c',
            marginBottom: '1rem',
          }}>
            Backend API Status
          </h2>

          {loading ? (
            <p style={{ color: '#718096' }}>Connecting to backend...</p>
          ) : apiHealth?.status === 'ok' ? (
            <div>
              <div style={{
                padding: '1rem',
                backgroundColor: '#f0fff4',
                border: '1px solid #9ae6b4',
                borderRadius: '8px',
                marginBottom: '1rem',
              }}>
                <p style={{ color: '#22543d', margin: 0 }}>
                  ✓ Successfully connected to backend API
                </p>
              </div>
              <pre style={{
                backgroundColor: '#f7fafc',
                padding: '1rem',
                borderRadius: '8px',
                overflow: 'auto',
                fontSize: '0.875rem',
              }}>
                {JSON.stringify(apiHealth, null, 2)}
              </pre>
            </div>
          ) : (
            <div style={{
              padding: '1rem',
              backgroundColor: '#fff5f5',
              border: '1px solid #feb2b2',
              borderRadius: '8px',
            }}>
              <p style={{ color: '#742a2a', marginBottom: '0.5rem' }}>
                ✗ Failed to connect to backend API
              </p>
              <p style={{ color: '#742a2a', fontSize: '0.875rem', margin: 0 }}>
                Make sure the engine is running at: {process.env.NEXT_PUBLIC_ENGINE_API_URL || 'http://localhost:8000'}
              </p>
            </div>
          )}
        </div>
      </div>
    </main>
  )
}

// Feature Card Component
function FeatureCard({
  title,
  description,
  status,
}: {
  title: string
  description: string
  status: 'planned' | 'in_progress' | 'completed'
}) {
  const statusColors = {
    planned: { bg: '#edf2f7', text: '#2d3748', badge: 'Planned' },
    in_progress: { bg: '#fef5e7', text: '#744210', badge: 'In Progress' },
    completed: { bg: '#f0fff4', text: '#22543d', badge: 'Ready' },
  }

  const colors = statusColors[status]

  return (
    <div style={{
      backgroundColor: 'white',
      borderRadius: '8px',
      padding: '1.5rem',
      boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
      border: '1px solid #e2e8f0',
    }}>
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'start',
        marginBottom: '0.75rem',
      }}>
        <h3 style={{
          fontSize: '1.125rem',
          fontWeight: '600',
          color: '#1a202c',
          margin: 0,
        }}>
          {title}
        </h3>
        <span style={{
          fontSize: '0.75rem',
          padding: '0.25rem 0.5rem',
          backgroundColor: colors.bg,
          color: colors.text,
          borderRadius: '4px',
          fontWeight: '500',
        }}>
          {colors.badge}
        </span>
      </div>
      <p style={{
        fontSize: '0.875rem',
        color: '#718096',
        lineHeight: '1.5',
        margin: 0,
      }}>
        {description}
      </p>
    </div>
  )
}
