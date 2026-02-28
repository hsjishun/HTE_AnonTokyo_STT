import axios, { AxiosError } from 'axios'
import type { TranscriptResult, FullAnalysisResult } from '../types'

const api = axios.create({ baseURL: '/api' })

function extractError(err: unknown): string {
  if (err instanceof AxiosError && err.response?.data) {
    const d = err.response.data as Record<string, unknown>
    if (typeof d.detail === 'string') return d.detail
  }
  if (err instanceof Error) return err.message
  return 'Unknown error'
}

export interface TranscribeFileOptions {
  file: File
  language: string
  onProgress?: (pct: number) => void
}

export interface TranscribeYoutubeOptions {
  url: string
  language: string
}

export interface FullAnalysisFileOptions {
  file: File
  language: string
  usePlaceholder: boolean
  onProgress?: (pct: number) => void
}

export interface FullAnalysisYoutubeOptions {
  url: string
  language: string
  usePlaceholder: boolean
}

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
      timeout: 10 * 60 * 1000,
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

export async function transcribeYoutube({
  url,
  language,
}: TranscribeYoutubeOptions): Promise<TranscriptResult> {
  try {
    const { data } = await api.post<TranscriptResult>('/analyze/youtube', {
      url,
      language,
    }, {
      timeout: 10 * 60 * 1000,
    })
    return data
  } catch (err) {
    throw new Error(extractError(err))
  }
}

export async function fullAnalysisFile({
  file,
  language,
  usePlaceholder,
  onProgress,
}: FullAnalysisFileOptions): Promise<FullAnalysisResult> {
  const form = new FormData()
  form.append('file', file)
  form.append('language', language)
  form.append('use_placeholder', String(usePlaceholder))

  try {
    const { data } = await api.post<FullAnalysisResult>('/full-analysis', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 30 * 60 * 1000,
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

export async function fullAnalysisYoutube({
  url,
  language,
  usePlaceholder,
}: FullAnalysisYoutubeOptions): Promise<FullAnalysisResult> {
  try {
    const { data } = await api.post<FullAnalysisResult>('/full-analysis/youtube', {
      url,
      language,
      use_placeholder: usePlaceholder,
    }, {
      timeout: 30 * 60 * 1000,
    })
    return data
  } catch (err) {
    throw new Error(extractError(err))
  }
}
