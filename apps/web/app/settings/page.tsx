'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { GlassCard, PrimaryButton, SecondaryButton } from '@/components/ui'
import { Navbar, Footer, PageShell, AuthWrapper } from '@/components/layout'
import { getCurrentUser } from '@/lib/supabaseClient'
import { signOut, updateProfile } from '@/lib/auth'

interface UserWithMetadata {
  email?: string
  id?: string
  user_metadata?: {
    display_name?: string
  }
}

function SettingsContent() {
  const router = useRouter()
  const [user, setUser] = useState<UserWithMetadata | null>(null)
  const [loggingOut, setLoggingOut] = useState(false)
  const [displayName, setDisplayName] = useState('')
  const [saving, setSaving] = useState(false)
  const [saveMessage, setSaveMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null)

  useEffect(() => {
    const fetchUser = async () => {
      const currentUser = await getCurrentUser()
      setUser(currentUser as UserWithMetadata)
      if (currentUser?.user_metadata?.display_name) {
        setDisplayName(currentUser.user_metadata.display_name)
      }
    }
    fetchUser()
  }, [])

  const handleLogout = async () => {
    setLoggingOut(true)
    await signOut()
    router.push('/')
  }

  const handleSaveProfile = async () => {
    if (!displayName.trim()) {
      setSaveMessage({ type: 'error', text: 'Name cannot be empty' })
      return
    }

    setSaving(true)
    setSaveMessage(null)

    const result = await updateProfile(displayName.trim())

    if (result.success) {
      setSaveMessage({ type: 'success', text: 'Profile updated successfully!' })
      // Update local user state
      setUser(prev => prev ? {
        ...prev,
        user_metadata: { ...prev.user_metadata, display_name: displayName.trim() }
      } : null)
    } else {
      setSaveMessage({ type: 'error', text: result.error?.message || 'Failed to update profile' })
    }

    setSaving(false)
  }

  // Get display name for UI
  const getUserDisplayName = () => {
    return user?.user_metadata?.display_name || user?.email?.split('@')[0] || 'User'
  }

  return (
    <>
      <Navbar user={user} onLogout={handleLogout} />

      <PageShell title="Settings" subtitle="Manage your account">
        <div className="max-w-2xl space-y-6">
          {/* Profile */}
          <GlassCard title="Profile">
            <div className="space-y-4">
              <div>
                <label htmlFor="displayName" className="block text-sm text-white/40 mb-1">
                  Display Name
                </label>
                <input
                  id="displayName"
                  type="text"
                  value={displayName}
                  onChange={(e) => setDisplayName(e.target.value)}
                  className="input-field"
                  placeholder="Your name"
                />
                <p className="text-white/30 text-xs mt-1">
                  This is how you&apos;ll appear throughout the app
                </p>
              </div>

              {saveMessage && (
                <div className={`p-3 rounded-lg text-sm ${
                  saveMessage.type === 'success'
                    ? 'bg-green-500/10 border border-green-500/20 text-green-400'
                    : 'bg-red-500/10 border border-red-500/20 text-red-400'
                }`}>
                  {saveMessage.text}
                </div>
              )}

              <PrimaryButton
                onClick={handleSaveProfile}
                disabled={saving}
                size="sm"
              >
                {saving ? 'Saving...' : 'Save Changes'}
              </PrimaryButton>
            </div>
          </GlassCard>

          {/* Account Info */}
          <GlassCard title="Account">
            <div className="space-y-4">
              <div>
                <label className="block text-sm text-white/40 mb-1">Email</label>
                <p className="text-white">{user?.email || 'Loading...'}</p>
              </div>

              <div>
                <label className="block text-sm text-white/40 mb-1">User ID</label>
                <p className="text-white font-mono text-sm">{user?.id || 'Loading...'}</p>
              </div>
            </div>
          </GlassCard>

          {/* API Configuration */}
          <GlassCard title="API Configuration">
            <div className="space-y-4">
              <div>
                <label className="block text-sm text-white/40 mb-1">Engine API URL</label>
                <p className="text-white font-mono text-sm break-all">
                  {process.env.NEXT_PUBLIC_ENGINE_API_URL || 'http://localhost:8000'}
                </p>
              </div>

              <div>
                <label className="block text-sm text-white/40 mb-1">Supabase Project</label>
                <p className="text-white font-mono text-sm break-all">
                  {process.env.NEXT_PUBLIC_SUPABASE_URL || 'Not configured'}
                </p>
              </div>
            </div>
          </GlassCard>

          {/* Usage / Billing (Placeholder) */}
          <GlassCard title="Usage & Billing">
            <div className="text-center py-8">
              <div className="text-4xl mb-4">📊</div>
              <h3 className="text-lg font-semibold text-white mb-2">Coming Soon</h3>
              <p className="text-white/60">
                Usage tracking and billing will be available in a future update.
              </p>
            </div>
          </GlassCard>

          {/* Logout */}
          <GlassCard title="Session">
            <p className="text-white/60 mb-4">
              Sign out of your account on this device.
            </p>
            <SecondaryButton
              onClick={handleLogout}
              disabled={loggingOut}
            >
              {loggingOut ? 'Signing out...' : 'Sign out'}
            </SecondaryButton>
          </GlassCard>

          {/* Danger Zone */}
          <GlassCard>
            <h3 className="text-lg font-semibold text-red-400 mb-4">Danger Zone</h3>
            <p className="text-white/60 mb-4">
              Permanently delete your account and all associated data.
            </p>
            <button
              className="px-4 py-2 rounded-lg text-red-400 border border-red-400/30 hover:bg-red-400/10 transition-colors"
              onClick={() => {
                alert('Account deletion is not yet implemented. Please contact support.')
              }}
            >
              Delete account
            </button>
          </GlassCard>
        </div>
      </PageShell>

      <Footer user={user} />
    </>
  )
}

export default function SettingsPage() {
  return (
    <AuthWrapper>
      <SettingsContent />
    </AuthWrapper>
  )
}
