import { createClient } from './supabaseClient'

/**
 * Auth helper functions for AuthorFlow Studios
 */

export interface AuthError {
  message: string
}

export interface AuthResult {
  success: boolean
  error?: AuthError
}

/**
 * Sign up with email, password, and optional display name
 */
export async function signUp(email: string, password: string, displayName?: string): Promise<AuthResult> {
  const supabase = createClient()

  const { error } = await supabase.auth.signUp({
    email,
    password,
    options: {
      emailRedirectTo: `${window.location.origin}/auth/callback`,
      data: {
        display_name: displayName || email.split('@')[0],
      },
    },
  })

  if (error) {
    return { success: false, error: { message: error.message } }
  }

  return { success: true }
}

/**
 * Update user profile (display name)
 */
export async function updateProfile(displayName: string): Promise<AuthResult> {
  const supabase = createClient()

  const { error } = await supabase.auth.updateUser({
    data: {
      display_name: displayName,
    },
  })

  if (error) {
    return { success: false, error: { message: error.message } }
  }

  return { success: true }
}

/**
 * Sign in with email and password
 */
export async function signIn(email: string, password: string): Promise<AuthResult> {
  const supabase = createClient()

  const { error } = await supabase.auth.signInWithPassword({
    email,
    password,
  })

  if (error) {
    return { success: false, error: { message: error.message } }
  }

  return { success: true }
}

/**
 * Sign in with magic link (passwordless)
 */
export async function signInWithMagicLink(email: string): Promise<AuthResult> {
  const supabase = createClient()

  const { error } = await supabase.auth.signInWithOtp({
    email,
    options: {
      emailRedirectTo: `${window.location.origin}/auth/callback`,
    },
  })

  if (error) {
    return { success: false, error: { message: error.message } }
  }

  return { success: true }
}

/**
 * Sign out the current user
 */
export async function signOut(): Promise<AuthResult> {
  const supabase = createClient()

  const { error } = await supabase.auth.signOut()

  if (error) {
    return { success: false, error: { message: error.message } }
  }

  return { success: true }
}

/**
 * Reset password (sends email)
 */
export async function resetPassword(email: string): Promise<AuthResult> {
  const supabase = createClient()

  const { error } = await supabase.auth.resetPasswordForEmail(email, {
    redirectTo: `${window.location.origin}/auth/reset-password`,
  })

  if (error) {
    return { success: false, error: { message: error.message } }
  }

  return { success: true }
}

/**
 * OAuth provider type
 */
export type OAuthProvider = 'google' | 'github'

/**
 * Sign in with OAuth provider (Google, GitHub)
 * Note: Requires configuring OAuth in Supabase Dashboard:
 * - Authentication > Providers > Enable Google/GitHub
 * - Add OAuth credentials from Google Cloud Console / GitHub Developer Settings
 */
export async function signInWithOAuth(provider: OAuthProvider): Promise<AuthResult> {
  const supabase = createClient()

  const { error } = await supabase.auth.signInWithOAuth({
    provider,
    options: {
      redirectTo: `${window.location.origin}/auth/callback`,
    },
  })

  if (error) {
    return { success: false, error: { message: error.message } }
  }

  return { success: true }
}
