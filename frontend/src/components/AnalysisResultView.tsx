import { useState } from 'react'
import {
  CheckCircle,
  RotateCcw,
  Download,
  Eye,
  BookOpen,
  Activity,
  ChevronDown,
  ChevronUp,
  Info,
} from 'lucide-react'
import type { FullAnalysisResult } from '../types'

interface Props {
  result: FullAnalysisResult
  onReset: () => void
}

type ActiveTab = 'body-language' | 'rubric' | 'transcript'

function downloadBlob(content: string, filename: string, mime: string) {
  const blob = new Blob([content], { type: mime })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

export default function AnalysisResultView({ result, onReset }: Props) {
  const [activeTab, setActiveTab] = useState<ActiveTab>('body-language')
  const [expandedSegment, setExpandedSegment] = useState<number | null>(0)

  const segments = result.body_language?.segments ?? []

  return (
    <div className="glass-card result-section">
      <div className="result-header">
        <div className="result-title">
          <CheckCircle />
          Analysis Complete
        </div>
        <div className="result-meta">
          {result.is_placeholder && (
            <span className="meta-chip placeholder-chip">
              <Info size={11} /> Demo Data
            </span>
          )}
          <span className="meta-chip">
            <Eye size={11} /> {segments.length} segments
          </span>
          <span className="meta-chip">
            <Activity size={11} /> {result.body_language?.model ?? 'N/A'}
          </span>
        </div>
      </div>

      <div className="view-tabs">
        <button
          className={`view-tab ${activeTab === 'body-language' ? 'active' : ''}`}
          onClick={() => setActiveTab('body-language')}
        >
          <span style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
            <Eye size={13} /> Body Language
          </span>
        </button>
        <button
          className={`view-tab ${activeTab === 'rubric' ? 'active' : ''}`}
          onClick={() => setActiveTab('rubric')}
        >
          <span style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
            <BookOpen size={13} /> Rubric Evaluation
          </span>
        </button>
        {result.transcript && (
          <button
            className={`view-tab ${activeTab === 'transcript' ? 'active' : ''}`}
            onClick={() => setActiveTab('transcript')}
          >
            <span style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
              <Activity size={13} /> Transcript
            </span>
          </button>
        )}
      </div>

      {activeTab === 'body-language' && (
        <div className="analysis-segments">
          {segments.map((seg) => {
            const isExpanded = expandedSegment === seg.segment
            return (
              <div
                key={seg.segment}
                className={`analysis-segment ${isExpanded ? 'expanded' : ''}`}
              >
                <button
                  className="segment-header-btn"
                  onClick={() =>
                    setExpandedSegment(isExpanded ? null : seg.segment)
                  }
                >
                  <span className="segment-label">
                    Segment {seg.segment}
                    <span className="segment-range">
                      {seg.start} &ndash; {seg.end}
                    </span>
                  </span>
                  {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                </button>
                {isExpanded && (
                  <div className="segment-body">
                    <div className="markdown-content">{seg.markdown}</div>
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}

      {activeTab === 'rubric' && (
        <div className="transcript-box" style={{ maxHeight: '500px' }}>
          {result.rubric_evaluation ?? 'No rubric evaluation available.'}
        </div>
      )}

      {activeTab === 'transcript' && result.transcript && (
        <div className="transcript-box">
          {result.transcript.full_text}
        </div>
      )}

      <div className="download-row">
        {result.body_language && (
          <button
            className="btn-download"
            onClick={() =>
              downloadBlob(
                result.body_language!.combined_report,
                'body_language_report.md',
                'text/markdown',
              )
            }
          >
            <Download /> Body Language .md
          </button>
        )}
        {result.rubric_evaluation && (
          <button
            className="btn-download"
            onClick={() =>
              downloadBlob(
                result.rubric_evaluation!,
                'rubric_evaluation.md',
                'text/markdown',
              )
            }
          >
            <Download /> Rubric .md
          </button>
        )}
        <button
          className="btn-download"
          onClick={() =>
            downloadBlob(
              JSON.stringify(result, null, 2),
              'full_analysis.json',
              'application/json',
            )
          }
        >
          <Download /> Full .json
        </button>
        <button className="btn-reset" onClick={onReset}>
          <RotateCcw /> New Analysis
        </button>
      </div>
    </div>
  )
}
