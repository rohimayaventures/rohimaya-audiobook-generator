'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { GlassCard, PrimaryButton, SecondaryButton } from '@/components/ui'
import { Navbar, Footer, PageShell, AuthWrapper } from '@/components/layout'
import { getCurrentUser } from '@/lib/supabaseClient'
import { signOut } from '@/lib/auth'

function SettingsContent() {
  const router = useRouter()
  const [user, setUser] = useState<{ email?: string; id?: string } | null>(null)
  const [loggingOut, setLoggingOut] = useState(false)

  useEffect(() => {
    const fetchUser = async () => {
      const currentUser = await getCurrentUser()
      setUser(currentUser)
    }
    fetchUser()
  }, [])

  const handleLogout = async () => {
    setLoggingOut(true)
    await signOut()
    router.push('/')
  }

  return (
    <>
      <Navbar user={user} onLogout={handleLogout} />

      <PageShell title="Settings" subtitle="Manage your account">
        <div className="max-w-2xl space-y-6">
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

      <Footer />
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
