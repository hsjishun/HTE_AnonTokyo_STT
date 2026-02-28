/**
 * API Service Module
 * 
 * Handles all HTTP communication with the backend:
 * - File transcription endpoint with progress tracking
 * - YouTube URL transcription endpoint
 * - Error handling and message extraction
 * 
 * API Endpoints:
 * - POST /api/analyze - File upload and transcription
 * - POST /api/analyze/youtube - YouTube URL transcription
 */
import axios, { AxiosError } from 'axios'
import type { TranscriptResult } from '../types'

const api = axios.create({ baseURL: '/api' })

/**
 * Extract a readable error message from API response
 * Handles various error formats to provide consistent user feedback
 */
function extractError(err: unknown): string {
  if (err instanceof AxiosError && err.response?.data) {
    const d = err.response.data as Record<string, unknown>
    if (typeof d.detail === 'string') return d.detail
  }
  if (err instanceof Error) return err.message
  return 'Unknown error'
}

/** Options for file-based transcription */
export interface TranscribeFileOptions {
  /** Audio/video file to transcribe */
  file: File
  /** Language code (e.g. 'en', 'auto' for auto-detect) */
  language: string
  /** Optional callback for upload progress (0-100%) */
  onProgress?: (pct: number) => void
}

/** Options for YouTube URL transcription */
export interface TranscribeYoutubeOptions {
  /** YouTube video URL to transcribe */
  url: string
  /** Language code (e.g. 'en', 'auto' for auto-detect) */
  language: string
}

/**
 * Transcribe an uploaded audio/video file
 * - Sends file as multipart form data
 * - Reports upload progress via callback
 * - Timeout: 10 minutes for long files
 */
export async function transcribeFile({
  file,
  language,
  onProgress,
}: TranscribeFileOptions): Promise<TranscriptResult> {
  const form = new FormData()
  form.append('file', file)
  form.append('language', language)

  try {
    const { data } = await api.post<TranscriptResult>('/analyze', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 10 * 60 * 1000, // 10 min for long files
      onUploadProgress(evt) {
        if (evt.total) {
          onProgress?.(Math.round((evt.loaded / evt.total) * 100))
        }
      },
    })
    return data
  } catch (err) {
    throw new Error(extractError(err))
  }
}

/**
 * Transcribe audio from a YouTube URL
 * - Downloads audio from YouTube
 * - Transcribes with language detection
 * - Timeout: 10 minutes for download + transcription
 */
export async function transcribeYoutube({
  url,
  language,
}: TranscribeYoutubeOptions): Promise<TranscriptResult> {
  try {
    const { data } = await api.post<TranscriptResult>('/analyze/youtube', {
      url,
      language,
    }, {
      timeout: 10 * 60 * 1000, // 10 min for download + transcribe
    })
    return data
  } catch (err) {
    throw new Error(extractError(err))
  }
}
