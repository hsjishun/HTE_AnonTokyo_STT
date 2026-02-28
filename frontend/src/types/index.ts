export type Theme = 'light' | 'dark'

export type InputMode = 'upload' | 'youtube'

export type AnalysisMode = 'transcribe' | 'full-analysis'

export type JobStatus =
  | 'idle'
  | 'uploading'
  | 'extracting'
  | 'transcribing'
  | 'analyzing'
  | 'evaluating'
  | 'done'
  | 'error'

export interface TranscriptSegment {
  start: number
  end: number
  text: string
}

export interface TranscriptResult {
  job_id: string
  language: string
  duration: number
  full_text: string
  segments: TranscriptSegment[]
  srt_content: string
}

export interface BodyLanguageSegmentReport {
  segment: number
  start: string
  end: string
  markdown: string
}

export interface BodyLanguageSummary {
  model: string
  total_segments: number
  segments: BodyLanguageSegmentReport[]
  combined_report: string
}

export interface FullAnalysisResult {
  status: string
  job_id: string
  video_source: string
  is_placeholder: boolean
  transcript: TranscriptResult | null
  body_language: BodyLanguageSummary | null
  rubric_evaluation: string | null
}

export interface ProgressState {
  status: JobStatus
  percent: number
  message: string
}
