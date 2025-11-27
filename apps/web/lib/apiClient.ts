/**
 * API Client for AuthorFlow Engine
 * Handles all communication with the backend FastAPI server
 */

const getBaseUrl = () => {
  const url = process.env.NEXT_PUBLIC_ENGINE_API_URL
  if (!url) {
    console.warn('NEXT_PUBLIC_ENGINE_API_URL is not set, using localhost:8000')
    return 'http://localhost:8000'
  }
  return url
}

/**
 * Generic fetch wrapper with error handling
 */
async function fetchApi<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const baseUrl = getBaseUrl()
  const url = `${baseUrl}${endpoint}`

  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
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
  title?: string
  filename?: string
  voice_profile?: string
  output_format?: string
  progress?: number
  error_message?: string
  audio_url?: string
  created_at: string
  updated_at?: string
  completed_at?: string
}

export interface CreateJobPayload {
  title?: string
  filename?: string
  manuscript_text?: string
  voice_profile?: string
  output_format?: string
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
 * Check API health
 */
export async function checkHealth(): Promise<HealthResponse> {
  return fetchApi<HealthResponse>('/health')
}

/**
 * Create a new audiobook generation job
 */
export async function createJob(
  payload: CreateJobPayload,
  file?: File
): Promise<Job> {
  const baseUrl = getBaseUrl()

  // If there's a file, use FormData
  if (file) {
    const formData = new FormData()
    formData.append('file', file)
    if (payload.title) formData.append('title', payload.title)
    if (payload.voice_profile) formData.append('voice_profile', payload.voice_profile)
    if (payload.output_format) formData.append('output_format', payload.output_format)

    const response = await fetch(`${baseUrl}/jobs`, {
      method: 'POST',
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
