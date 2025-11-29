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
    // Try to parse error response, handle empty bodies
    let error: { message?: string; detail?: string } = { message: 'Request failed' }
    try {
      const text = await response.text()
      if (text && text.trim()) {
        error = JSON.parse(text)
      }
    } catch {
      // Ignore JSON parse errors for error responses
    }
    throw new Error(error.detail || error.message || `HTTP ${response.status}`)
  }

  // Handle empty responses (e.g., 204 No Content)
  const contentLength = response.headers.get('content-length')
  if (response.status === 204 || contentLength === '0') {
    return {} as T
  }

  // Try to parse JSON, return empty object if body is empty
  const text = await response.text()
  if (!text || text.trim() === '') {
    return {} as T
  }

  try {
    return JSON.parse(text) as T
  } catch {
    return {} as T
  }
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
  retry_count?: number
  created_at: string
  started_at?: string
  completed_at?: string
  // Cover art fields
  generate_cover?: boolean
  cover_vibe?: string
  cover_image_provider?: string
  has_cover?: boolean
  cover_image_path?: string
}

export interface CreateJobPayload {
  title: string
  author?: string
  // Source types: 'upload', 'paste', 'google_drive'
  source_type: 'upload' | 'paste' | 'google_drive'
  source_path?: string
  manuscript_text?: string
  // Modes: single_voice, dual_voice, findaway, multi_character
  mode: 'single_voice' | 'dual_voice' | 'findaway' | 'multi_character'
  // TTS provider: 'google' (Gemini) or 'openai'
  tts_provider: 'google' | 'openai'
  // Voice selection - either narrator_voice_id (legacy) or voice_preset_id (new)
  narrator_voice_id: string
  voice_preset_id?: string
  character_voice_id?: string
  character_name?: string
  audio_format?: string
  audio_bitrate?: string
  // Multilingual TTS settings
  input_language_code?: string  // e.g., "en-US", "es-ES", "auto"
  output_language_code?: string // e.g., "en-US", "mr-IN" (for translation)
  emotion_style_prompt?: string // e.g., "soft, romantic, intimate"
  // Findaway-specific options
  narrator_name?: string
  genre?: string
  language?: string
  isbn?: string
  publisher?: string
  sample_style?: 'default' | 'spicy' | 'ultra_spicy'
  // Cover art generation
  generate_cover?: boolean
  cover_vibe?: string
  cover_image_provider?: 'openai' | 'banana'
}

export interface CloneJobPayload {
  title?: string
  narrator_voice_id?: string
  mode?: 'single_voice' | 'dual_voice' | 'findaway' | 'multi_character'
}

export interface SystemStatus {
  api_version: string
  environment: string
  uptime_seconds?: number
  worker_running: boolean
  queued_jobs: number
  processing_jobs: number
  processing_job_ids: string[]
  total_jobs: number
  pending_jobs: number
  processing_jobs_db: number
  completed_jobs: number
  failed_jobs: number
  total_users: number
  active_subscriptions: number
  google_drive_enabled: boolean
  emotional_tts_enabled: boolean
  banana_cover_enabled: boolean
  recent_errors: Array<{
    job_id: string
    title: string
    error: string
    timestamp: string
  }>
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

  // If there's a file, use FormData and the /jobs/upload endpoint
  if (file) {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('title', payload.title || file.name.replace(/\.[^/.]+$/, ''))
    formData.append('source_type', payload.source_type)
    formData.append('mode', payload.mode)
    formData.append('tts_provider', payload.tts_provider)
    formData.append('narrator_voice_id', payload.narrator_voice_id)
    formData.append('audio_format', payload.audio_format || 'mp3')
    formData.append('audio_bitrate', payload.audio_bitrate || '128k')

    const response = await fetch(`${baseUrl}/jobs/upload`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
      body: formData,
    })

    if (!response.ok) {
      // Try to parse error response, handle empty bodies
      let error: { message?: string; detail?: string } = { message: 'Upload failed' }
      try {
        const text = await response.text()
        if (text && text.trim()) {
          error = JSON.parse(text)
        }
      } catch {
        // Ignore JSON parse errors
      }
      throw new Error(error.detail || error.message || `HTTP ${response.status}`)
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

/**
 * Retry a failed job
 */
export async function retryJob(id: string): Promise<Job> {
  return fetchApi<Job>(`/jobs/${id}/retry`, {
    method: 'POST',
  })
}

/**
 * Clone an existing job with optional modifications
 */
export async function cloneJob(id: string, payload?: CloneJobPayload): Promise<Job> {
  return fetchApi<Job>(`/jobs/${id}/clone`, {
    method: 'POST',
    body: JSON.stringify(payload || {}),
  })
}

/**
 * Get system status (admin only)
 */
export async function getSystemStatus(): Promise<SystemStatus> {
  return fetchApi<SystemStatus>('/admin/status')
}

// ============================================
// Google Drive Integration
// ============================================

export interface GoogleDriveStatus {
  connected: boolean
  has_tokens: boolean
  configured: boolean
}

export interface GoogleDriveFile {
  id: string
  name: string
  mimeType: string
  size?: string
  modifiedTime?: string
  webViewLink?: string
}

export interface GoogleDriveFilesResponse {
  files: GoogleDriveFile[]
  nextPageToken?: string
}

/**
 * Get Google Drive OAuth URL for connecting
 */
export async function getGoogleDriveAuthUrl(): Promise<{ auth_url: string }> {
  return fetchApi<{ auth_url: string }>('/google-drive/auth-url')
}

/**
 * Check Google Drive connection status
 */
export async function getGoogleDriveStatus(): Promise<GoogleDriveStatus> {
  return fetchApi<GoogleDriveStatus>('/google-drive/status')
}

/**
 * List files from Google Drive
 */
export async function listGoogleDriveFiles(params?: {
  pageToken?: string
  pageSize?: number
}): Promise<GoogleDriveFilesResponse> {
  const searchParams = new URLSearchParams()
  if (params?.pageToken) searchParams.set('page_token', params.pageToken)
  if (params?.pageSize) searchParams.set('page_size', params.pageSize.toString())

  const query = searchParams.toString()
  const endpoint = query ? `/google-drive/files?${query}` : '/google-drive/files'

  return fetchApi<GoogleDriveFilesResponse>(endpoint)
}

/**
 * Import a file from Google Drive as manuscript
 */
export async function importGoogleDriveFile(fileId: string): Promise<{
  success: boolean
  file_id: string
  filename: string
  text_length: number
  manuscript_path: string
}> {
  return fetchApi('/google-drive/import', {
    method: 'POST',
    body: JSON.stringify({ file_id: fileId }),
  })
}

/**
 * Disconnect Google Drive (remove tokens)
 */
export async function disconnectGoogleDrive(): Promise<{ success: boolean; message: string }> {
  return fetchApi<{ success: boolean; message: string }>('/google-drive/disconnect', {
    method: 'DELETE',
  })
}

// ============================================
// Cover Art
// ============================================

export interface CoverArtResponse {
  has_cover: boolean
  cover_url?: string
  cover_path?: string
}

/**
 * Get cover art URL for a job
 */
export async function getJobCoverUrl(jobId: string): Promise<CoverArtResponse> {
  return fetchApi<CoverArtResponse>(`/jobs/${jobId}/cover`)
}

// ============================================
// TTS Voice Library
// ============================================

export interface VoicePreset {
  id: string
  label: string
  description: string
  voice_name: string
  default_language_code: string
  gender: string
  style: string
}

export interface LanguageInfo {
  code: string
  name: string
}

export interface VoiceLibraryResponse {
  voice_presets: VoicePreset[]
  input_languages: LanguageInfo[]
  output_languages: LanguageInfo[]
}

export interface TTSPreviewRequest {
  text?: string
  preset_id: string
  input_language_code: string
  output_language_code?: string
  emotion_style_prompt?: string
}

export interface TTSPreviewResponse {
  success: boolean
  audio_url?: string
  audio_base64?: string
  preset_id: string
  input_language: string
  output_language: string
  duration_estimate_seconds?: number
  error?: string
}

/**
 * Get available voice presets and languages
 */
export async function getVoiceLibrary(): Promise<VoiceLibraryResponse> {
  return fetchApi<VoiceLibraryResponse>('/tts/voices')
}

/**
 * Generate a TTS voice preview
 */
export async function previewTTSVoice(request: TTSPreviewRequest): Promise<TTSPreviewResponse> {
  return fetchApi<TTSPreviewResponse>('/tts/preview', {
    method: 'POST',
    body: JSON.stringify(request),
  })
}
