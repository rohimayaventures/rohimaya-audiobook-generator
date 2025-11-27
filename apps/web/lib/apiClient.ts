/**
 * API Client for AuthorFlow Engine
 * Handles all communication with the backend FastAPI server
 */

import { getSession } from './supabaseClient'

const getBaseUrl = () => {
  const url = process.env.NEXT_PUBLIC_ENGINE_API_URL
  if (!url) {
    console.warn('NEXT_PUBLIC_ENGINE_API_URL is not set, using localhost:8000')
    return 'http://localhost:8000'
  }
  return url
}

/**
 * Get the current user's access token from Supabase session
 */
async function getAuthToken(): Promise<string | null> {
  const session = await getSession()
  return session?.access_token || null
}

/**
 * Generic fetch wrapper with error handling and authentication
 */
async function fetchApi<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const baseUrl = getBaseUrl()
  const url = `${baseUrl}${endpoint}`

  // Get auth token
  const token = await getAuthToken()
  if (!token) {
    throw new Error('Not authenticated. Please log in.')
  }

  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
      ...options.headers,
    },
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: 'Request failed' }))
    throw new Error(error.detail || error.message || `HTTP ${response.status}`)
  }

  return response.json()
}

// ============================================
// Types
// ============================================

export interface Job {
  id: string
  user_id: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  mode: string
  title: string
  author?: string
  source_type: string
  source_path?: string
  tts_provider: string
  narrator_voice_id: string
  character_voice_id?: string
  character_name?: string
  audio_format: string
  audio_bitrate: string
  audio_path?: string
  duration_seconds?: number
  file_size_bytes?: number
  progress_percent?: number
  error_message?: string
  created_at: string
  started_at?: string
  completed_at?: string
}

export interface CreateJobPayload {
  title: string
  author?: string
  source_type: 'upload' | 'paste' | 'google_drive' | 'url'
  source_path?: string
  manuscript_text?: string
  mode: 'single_voice' | 'dual_voice'
  tts_provider: 'openai' | 'elevenlabs' | 'inworld'
  narrator_voice_id: string
  character_voice_id?: string
  character_name?: string
  audio_format?: string
  audio_bitrate?: string
}

export interface HealthResponse {
  status: string
  service: string
  version: string
  timestamp: string
}

// ============================================
// API Functions
// ============================================

/**
 * Check API health (no auth required)
 */
export async function checkHealth(): Promise<HealthResponse> {
  const baseUrl = getBaseUrl()
  const response = await fetch(`${baseUrl}/health`)
  if (!response.ok) {
    throw new Error('Health check failed')
  }
  return response.json()
}

/**
 * Create a new audiobook generation job
 */
export async function createJob(
  payload: CreateJobPayload,
  file?: File
): Promise<Job> {
  const baseUrl = getBaseUrl()

  // Get auth token
  const token = await getAuthToken()
  if (!token) {
    throw new Error('Not authenticated. Please log in.')
  }

  // If there's a file, use FormData
  if (file) {
    const formData = new FormData()
    formData.append('file', file)
    if (payload.title) formData.append('title', payload.title)
    formData.append('source_type', payload.source_type)
    formData.append('mode', payload.mode)
    formData.append('tts_provider', payload.tts_provider)
    formData.append('narrator_voice_id', payload.narrator_voice_id)
    if (payload.audio_format) formData.append('audio_format', payload.audio_format)
    if (payload.audio_bitrate) formData.append('audio_bitrate', payload.audio_bitrate)

    const response = await fetch(`${baseUrl}/jobs`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
      body: formData,
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({ message: 'Upload failed' }))
      throw new Error(error.detail || error.message)
    }

    return response.json()
  }

  // Otherwise send JSON
  return fetchApi<Job>('/jobs', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

/**
 * Get all jobs for the current user
 */
export async function getJobs(params?: {
  status?: string
  limit?: number
  offset?: number
}): Promise<Job[]> {
  const searchParams = new URLSearchParams()
  if (params?.status) searchParams.set('status', params.status)
  if (params?.limit) searchParams.set('limit', params.limit.toString())
  if (params?.offset) searchParams.set('offset', params.offset.toString())

  const query = searchParams.toString()
  const endpoint = query ? `/jobs?${query}` : '/jobs'

  return fetchApi<Job[]>(endpoint)
}

/**
 * Get a specific job by ID
 */
export async function getJob(id: string): Promise<Job> {
  return fetchApi<Job>(`/jobs/${id}`)
}

/**
 * Get download URL for a completed job
 */
export async function getJobDownloadUrl(id: string): Promise<{ url: string }> {
  return fetchApi<{ url: string }>(`/jobs/${id}/download`)
}

/**
 * Download job file directly
 */
export function getDownloadUrl(id: string): string {
  const baseUrl = getBaseUrl()
  return `${baseUrl}/jobs/${id}/download`
}

/**
 * Cancel a job
 */
export async function cancelJob(id: string): Promise<{ message: string }> {
  return fetchApi<{ message: string }>(`/jobs/${id}/cancel`, {
    method: 'POST',
  })
}

/**
 * Delete a job
 */
export async function deleteJob(id: string): Promise<{ message: string }> {
  return fetchApi<{ message: string }>(`/jobs/${id}`, {
    method: 'DELETE',
  })
}
