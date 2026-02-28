/**
 * Application Type Definitions
 * 
 * Core types used throughout the VoiceTrace application for type safety
 */

/** UI theme setting */
export type Theme = 'light' | 'dark'

/** User input method selection */
export type InputMode = 'upload' | 'youtube'

/** Transcription job lifecycle states */
export type JobStatus =
  | 'idle'
  | 'uploading'
  | 'extracting'
  | 'transcribing'
  | 'done'
  | 'error'

/** Individual transcript segment with timing information */
export interface TranscriptSegment {
  /** Start time in seconds */
  start: number
  /** End time in seconds */
  end: number
  /** Transcribed text for this segment */
  text: string
}

/** Complete transcription result from API */
export interface TranscriptResult {
  job_id: string
  language: string
  duration: number
  full_text: string
  segments: TranscriptSegment[]
  srt_content: string
}

/** Current progress state for active transcription job */
export interface ProgressState {
  status: JobStatus
  percent: number
  message: string
}
