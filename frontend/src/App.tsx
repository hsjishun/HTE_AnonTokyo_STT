import { useState } from 'react'
import { useTheme } from './hooks/useTheme'
import Header from './components/Header'
import UploadSection from './components/UploadSection'
import ProgressBar from './components/ProgressBar'
import ResultView from './components/ResultView'
import AnalysisResultView from './components/AnalysisResultView'
import {
  transcribeFile,
  transcribeYoutube,
  fullAnalysisFile,
  fullAnalysisYoutube,
} from './services/api'
import type {
  AnalysisMode,
  InputMode,
  ProgressState,
  TranscriptResult,
  FullAnalysisResult,
} from './types'

const IDLE_PROGRESS: ProgressState = { status: 'idle', percent: 0, message: '' }

export default function App() {
  const { theme, toggle } = useTheme()

  const [analysisMode, setAnalysisMode] = useState<AnalysisMode>('full-analysis')
  const [inputMode, setInputMode] = useState<InputMode>('upload')
  const [file, setFile] = useState<File | null>(null)
  const [youtubeUrl, setYoutubeUrl] = useState('')
  const [language, setLanguage] = useState('auto')

  const [progress, setProgress] = useState<ProgressState>(IDLE_PROGRESS)
  const [transcriptResult, setTranscriptResult] = useState<TranscriptResult | null>(null)
  const [analysisResult, setAnalysisResult] = useState<FullAnalysisResult | null>(null)

  const isProcessing =
    progress.status !== 'idle' &&
    progress.status !== 'done' &&
    progress.status !== 'error'

  const handleSubmit = async () => {
    setTranscriptResult(null)
    setAnalysisResult(null)

    try {
      if (analysisMode === 'transcribe') {
        await handleTranscribe()
      } else {
        await handleFullAnalysis()
      }
    } catch (err: unknown) {
      const message =
        err instanceof Error
          ? err.message
          : 'An unexpected error occurred. Please try again.'
      setProgress({ status: 'error', percent: 0, message })
    }
  }

  const handleTranscribe = async () => {
    if (inputMode === 'upload' && file) {
      setProgress({ status: 'uploading', percent: 5, message: 'Uploading file...' })
      const data = await transcribeFile({
        file,
        language,
        onProgress: pct => {
          if (pct < 100) {
            setProgress({ status: 'uploading', percent: Math.round(pct * 0.35), message: 'Uploading file...' })
          } else {
            setProgress({ status: 'extracting', percent: 40, message: 'Extracting audio track...' })
            setTimeout(() => {
              setProgress({ status: 'transcribing', percent: 65, message: 'Transcribing with AI...' })
            }, 800)
          }
        },
      })
      setProgress({ status: 'done', percent: 100, message: 'Transcription complete!' })
      setTranscriptResult(data)
    } else if (inputMode === 'youtube' && youtubeUrl.trim()) {
      setProgress({ status: 'uploading', percent: 10, message: 'Fetching YouTube video...' })
      setTimeout(() => setProgress({ status: 'extracting', percent: 35, message: 'Extracting audio...' }), 1200)
      setTimeout(() => setProgress({ status: 'transcribing', percent: 60, message: 'Transcribing with AI...' }), 3000)
      const data = await transcribeYoutube({ url: youtubeUrl.trim(), language })
      setProgress({ status: 'done', percent: 100, message: 'Transcription complete!' })
      setTranscriptResult(data)
    }
  }

  const handleFullAnalysis = async () => {
    if (inputMode === 'upload' && file) {
      setProgress({ status: 'uploading', percent: 5, message: 'Uploading file...' })
      const data = await fullAnalysisFile({
        file,
        language,
        usePlaceholder: true,
        onProgress: pct => {
          if (pct < 100) {
            setProgress({ status: 'uploading', percent: Math.round(pct * 0.2), message: 'Uploading file...' })
          } else {
            setProgress({ status: 'analyzing', percent: 50, message: 'Analyzing body language & pedagogy...' })
          }
        },
      })
      setProgress({ status: 'done', percent: 100, message: 'Analysis complete!' })
      setAnalysisResult(data)
    } else if (inputMode === 'youtube' && youtubeUrl.trim()) {
      setProgress({ status: 'uploading', percent: 10, message: 'Fetching YouTube video...' })
      setTimeout(() => setProgress({ status: 'analyzing', percent: 40, message: 'Analyzing body language...' }), 1500)
      setTimeout(() => setProgress({ status: 'evaluating', percent: 70, message: 'Running rubric evaluation...' }), 3000)
      const data = await fullAnalysisYoutube({
        url: youtubeUrl.trim(),
        language,
        usePlaceholder: true,
      })
      setProgress({ status: 'done', percent: 100, message: 'Analysis complete!' })
      setAnalysisResult(data)
    }
  }

  const handleReset = () => {
    setProgress(IDLE_PROGRESS)
    setTranscriptResult(null)
    setAnalysisResult(null)
    setFile(null)
    setYoutubeUrl('')
  }

  const hasResult = transcriptResult || analysisResult

  return (
    <div className="app-wrapper">
      <Header theme={theme} onToggle={toggle} />

      <main className="main-content">
        <section className="hero">
          <div className="hero-eyebrow">Powered by AI</div>
          <h1>
            Teacher Performance<br />
            <span>Analysis Dashboard</span>
          </h1>
          <p className="hero-desc">
            Upload a classroom video or paste a YouTube link — get transcription,
            body language analysis, and rubric-based evaluation powered by Gemini AI.
          </p>
        </section>

        {!hasResult && (
          <div className="glass-card">
            <UploadSection
              analysisMode={analysisMode}
              onAnalysisModeChange={setAnalysisMode}
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

        {progress.status !== 'idle' && !hasResult && (
          <ProgressBar progress={progress} />
        )}

        {transcriptResult && (
          <ResultView result={transcriptResult} onReset={handleReset} />
        )}

        {analysisResult && (
          <AnalysisResultView result={analysisResult} onReset={handleReset} />
        )}
      </main>

      <footer className="footer">
        HTE AnonTokyo — Teacher Performance Dashboard &nbsp;&middot;&nbsp; {new Date().getFullYear()}
      </footer>
    </div>
  )
}
