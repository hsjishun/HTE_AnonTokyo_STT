/**
 * VoiceTrace Main Application Component
 * 
 * Core application component that orchestrates the transcription workflow:
 * - Manages input mode selection (file upload vs YouTube URL)
 * - Handles file and URL input state
 * - Coordinates API calls and progress tracking
 * - Displays results and error states
 * - Integrates theme switching functionality
 */
import { useState } from 'react'
import { useTheme } from './hooks/useTheme'
import Header from './components/Header'
import UploadSection from './components/UploadSection'
import ProgressBar from './components/ProgressBar'
import ResultView from './components/ResultView'
import { transcribeFile, transcribeYoutube } from './services/api'
import type { InputMode, ProgressState, TranscriptResult } from './types'

/** Default idle state for progress indicator - used when no transcription is in progress */
const IDLE_PROGRESS: ProgressState = { status: 'idle', percent: 0, message: '' }

export default function App() {
  const { theme, toggle } = useTheme()

  // ──────────────────────────────────────────────────────────────────────────
  // User Input State
  // ──────────────────────────────────────────────────────────────────────────
  /** Tracks which input method user has selected: file upload or YouTube URL */
  const [inputMode, setInputMode] = useState<InputMode>('upload')
  /** File object when user selects a file for upload */
  const [file, setFile] = useState<File | null>(null)
  /** YouTube URL entered by user */
  const [youtubeUrl, setYoutubeUrl] = useState('')
  /** Language preference for transcription (defaults to auto-detect) */
  const [language, setLanguage] = useState('auto')

  // ──────────────────────────────────────────────────────────────────────────
  // Job State
  // ──────────────────────────────────────────────────────────────────────────
  /** Tracks current progress: status, completion percentage, and user-facing message */
  const [progress, setProgress] = useState<ProgressState>(IDLE_PROGRESS)
  /** Final transcription result with transcript segments and metadata */
  const [result, setResult] = useState<TranscriptResult | null>(null)

  /** Computed flag indicating whether transcription is actively processing */
  const isProcessing =
    progress.status !== 'idle' &&
    progress.status !== 'done' &&
    progress.status !== 'error'

  /**
   * Handle transcription submission
   * - Routes to file upload or YouTube URL transcription
   * - Manages progress state updates
   * - Handles errors with user-friendly messages
   */
  const handleSubmit = async () => {
    setResult(null)

    try {
      if (inputMode === 'upload' && file) {
        setProgress({ status: 'uploading', percent: 5, message: 'Uploading file…' })

        const data = await transcribeFile({
          file,
          language,
          onProgress: pct => {
            if (pct < 100) {
              setProgress({ status: 'uploading', percent: Math.round(pct * 0.35), message: 'Uploading file…' })
            } else {
              setProgress({ status: 'extracting', percent: 40, message: 'Extracting audio track…' })
              // Simulate extracting → transcribing stages  
              setTimeout(() => {
                setProgress({ status: 'transcribing', percent: 65, message: 'Transcribing with AI…' })
              }, 800)
            }
          },
        })

        setProgress({ status: 'done', percent: 100, message: 'Transcription complete!' })
        setResult(data)
      } else if (inputMode === 'youtube' && youtubeUrl.trim()) {
        setProgress({ status: 'uploading', percent: 10, message: 'Fetching YouTube video…' })

        setTimeout(() => setProgress({ status: 'extracting', percent: 35, message: 'Extracting audio…' }), 1200)
        setTimeout(() => setProgress({ status: 'transcribing', percent: 60, message: 'Transcribing with AI…' }), 3000)

        const data = await transcribeYoutube({ url: youtubeUrl.trim(), language })

        setProgress({ status: 'done', percent: 100, message: 'Transcription complete!' })
        setResult(data)
      }
    } catch (err: unknown) {
      const message =
        err instanceof Error
          ? err.message
          : 'An unexpected error occurred. Please try again.'
      setProgress({ status: 'error', percent: 0, message })
    }
  }

  /**
   * Reset the application to initial state
   * Clears all input fields, progress tracking, and results
   */
  const handleReset = () => {
    setProgress(IDLE_PROGRESS)
    setResult(null)
    setFile(null)
    setYoutubeUrl('')
  }

  return (
    <div className="app-wrapper">
      <Header theme={theme} onToggle={toggle} />

      <main className="main-content">
        {/* Hero */}
        <section className="hero">
          <div className="hero-eyebrow">✦ Powered by AI</div>
          <h1>
            Turn any video into<br />
            <span>accurate text</span>
          </h1>
          <p className="hero-desc">
            Upload a video file or paste a YouTube link — we'll extract the audio
            and transcribe it in seconds. Download as&nbsp;.txt, .srt, or&nbsp;.json.
          </p>
        </section>

        {/* Input card — hidden when showing results */}
        {!result && (
          <div className="glass-card">
            <UploadSection
              inputMode={inputMode}
              onModeChange={setInputMode}
              file={file}
              onFileChange={setFile}
              youtubeUrl={youtubeUrl}
              onYoutubeUrlChange={setYoutubeUrl}
              language={language}
              onLanguageChange={setLanguage}
              onSubmit={handleSubmit}
              isDisabled={isProcessing}
            />
          </div>
        )}

        {/* Progress */}
        {progress.status !== 'idle' && !result && (
          <ProgressBar progress={progress} />
        )}

        {/* Results */}
        {result && (
          <ResultView result={result} onReset={handleReset} />
        )}
      </main>

      <footer className="footer">
        VoiceTrace — HTE AnonTokyo &nbsp;·&nbsp; {new Date().getFullYear()}
      </footer>
    </div>
  )
}
