import React, { useState, useEffect, useRef } from 'react'
import { RefreshCw, Copy, Check, Search, Terminal } from 'lucide-react'
import { api } from '../api/client'
import { useToast } from '../context/ToastContext'
import type { ServiceStatus } from '../types/api'

interface LogViewerProps {
  services: ServiceStatus[]
  selectedServiceId: string
  onSelectService: (id: string) => void
}

// Rich syntax highlighter for terminal logs
const renderColoredLine = (rawLine: string) => {
  // Separator lines
  if (/^[=\-_]{8,}$/.test(rawLine.trim())) {
    return <span className="text-stone-600 font-bold">{rawLine}</span>
  }

  // Regex for timestamp at beginning: [YYYY-MM-DD ...] or DD-Mon-YYYY ... or ISO timestamp
  const tsMatch = rawLine.match(/^(\[?\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:[+-]\d{2}:\d{2}|Z)?\]?|\d{1,2}-[A-Za-z]{3}-\d{4} \d{1,2}:\d{2}:\d{2} [AP]M|\d{1,2}\/\d{1,2}\/\d{2,4} \d{1,2}:\d{2}:\d{2})/i)

  let timestamp = ''
  let rest = rawLine
  if (tsMatch) {
    timestamp = tsMatch[0]
    rest = rawLine.slice(timestamp.length)
  }

  // Check log level in rest: [INFO], [ERROR], [WARNING], INFO:, etc.
  const levelMatch = rest.match(/(\[(?:ERROR|WARNING|WARN|INFO|DEBUG|SUCCESS|CRITICAL)\]|(?:ERROR|WARNING|WARN|INFO|DEBUG|SUCCESS|CRITICAL):)/i)
  let level = ''
  let beforeLevel = ''
  let afterLevel = rest
  if (levelMatch && levelMatch.index !== undefined) {
    beforeLevel = rest.slice(0, levelMatch.index)
    level = levelMatch[0]
    afterLevel = rest.slice(levelMatch.index + level.length)
  }

  const getLevelStyle = (lvl: string) => {
    const upper = lvl.toUpperCase()
    if (upper.includes('ERROR') || upper.includes('CRITICAL')) {
      return 'text-rose-400 font-semibold bg-rose-500/20 px-1 py-0.5 rounded border border-rose-500/30'
    }
    if (upper.includes('WARN')) {
      return 'text-amber-300 font-semibold bg-amber-500/20 px-1 py-0.5 rounded border border-amber-500/30'
    }
    if (upper.includes('INFO')) {
      return 'text-sky-300 font-medium bg-sky-500/15 px-1 py-0.5 rounded border border-sky-500/30'
    }
    if (upper.includes('SUCCESS')) {
      return 'text-emerald-400 font-semibold bg-emerald-500/20 px-1 py-0.5 rounded border border-emerald-500/30'
    }
    return 'text-stone-400'
  }

  // Tokenize rest content
  const highlightContent = (text: string) => {
    const regex = /(https?:\/\/[^\s]+|wss?:\/\/[^\s]+|\b(?:GET|POST|PUT|DELETE|PATCH|OPTIONS|HEAD)\b|\b(?:200 OK|HTTP\/1\.[01] 200|200|201|204|400|401|403|404|422|500|502|503)\b|\b(?:listening at|listening on|connected|startup complete|ready in|WiredTiger|MongoDB starting|Application startup|Uvicorn running|STOPPED|STARTING)\b|\b(?:Traceback|Exception|Error|failed|invalid_grant)\b)/gi

    const parts = text.split(regex)
    return parts.map((part, i) => {
      if (!part) return null
      const lower = part.toLowerCase()

      // URLs
      if (lower.startsWith('http://') || lower.startsWith('https://') || lower.startsWith('ws://') || lower.startsWith('wss://')) {
        return <span key={i} className="text-cyan-400 underline decoration-cyan-500/40">{part}</span>
      }
      // HTTP Methods
      if (/^(GET|POST|PUT|DELETE|PATCH|OPTIONS|HEAD)$/i.test(part)) {
        return <span key={i} className="text-indigo-400 font-bold">{part}</span>
      }
      // Status 200 OK
      if (part === '200 OK' || part.includes('200') || part === '201') {
        return <span key={i} className="text-emerald-400 font-bold">{part}</span>
      }
      // Status 4xx
      if (/^(400|401|403|404|422)$/.test(part)) {
        return <span key={i} className="text-amber-400 font-bold">{part}</span>
      }
      // Status 5xx
      if (/^(500|502|503)$/.test(part)) {
        return <span key={i} className="text-rose-400 font-bold">{part}</span>
      }
      // Lifecycle positive keywords
      if (lower.includes('listening') || lower.includes('connected') || lower.includes('ready in') || lower.includes('startup') || lower.includes('starting')) {
        return <span key={i} className="text-emerald-300 font-medium">{part}</span>
      }
      // Error keywords
      if (lower.includes('error') || lower.includes('traceback') || lower.includes('exception') || lower.includes('failed') || lower.includes('stopped') || lower.includes('invalid_grant')) {
        return <span key={i} className="text-rose-400 font-semibold">{part}</span>
      }

      // Default text
      return <span key={i} className="text-stone-300">{part}</span>
    })
  }

  return (
    <span>
      {timestamp && <span className="text-stone-500 mr-2 select-none">{timestamp}</span>}
      {beforeLevel && highlightContent(beforeLevel)}
      {level && <span className={`mx-1.5 ${getLevelStyle(level)}`}>{level}</span>}
      {afterLevel && highlightContent(afterLevel)}
    </span>
  )
}

export const LogViewer: React.FC<LogViewerProps> = ({
  services,
  selectedServiceId,
  onSelectService,
}) => {
  const { success, error } = useToast()
  const [lines, setLines] = useState<string[]>([])
  const [tail, setTail] = useState<number>(150)
  const [isLoading, setIsLoading] = useState<boolean>(false)
  const [autoRefresh, setAutoRefresh] = useState<boolean>(true)
  const [searchTerm, setSearchTerm] = useState<string>('')
  const [copied, setCopied] = useState<boolean>(false)
  const terminalEndRef = useRef<HTMLDivElement>(null)

  const fetchLogs = async (silent: boolean = false) => {
    if (!selectedServiceId) return
    if (!silent) setIsLoading(true)
    try {
      const res = await api.getLogs(selectedServiceId, tail)
      setLines(res.lines || [])
    } catch (err: any) {
      if (!silent) error('Log Read Failed', err.message)
    } finally {
      if (!silent) setIsLoading(false)
    }
  }

  useEffect(() => {
    fetchLogs(false)
  }, [selectedServiceId, tail])

  useEffect(() => {
    if (!autoRefresh) return
    const interval = setInterval(() => {
      fetchLogs(true)
    }, 2500)
    return () => clearInterval(interval)
  }, [autoRefresh, selectedServiceId, tail])

  const handleCopy = () => {
    navigator.clipboard.writeText(lines.join('\n'))
    setCopied(true)
    success('Copied', 'Log lines copied to clipboard.')
    setTimeout(() => setCopied(false), 2000)
  }

  const filteredLines = searchTerm
    ? lines.filter(line => line.toLowerCase().includes(searchTerm.toLowerCase()))
    : lines

  return (
    <div className="rounded-2xl border border-black/[0.06] dark:border-white/[0.08] bg-white dark:bg-[#181915] p-4 shadow-soft">
      {/* Sleek Toolbar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-3">
        {/* Left: Service Select */}
        <div className="flex items-center gap-2 shrink-0">
          <Terminal className="h-4 w-4 text-stone-500 shrink-0" />
          <select
            value={selectedServiceId}
            onChange={e => onSelectService(e.target.value)}
            className="focus-ring rounded-xl bg-stone-100 dark:bg-stone-800/80 px-3 py-1.5 text-xs font-semibold font-sans text-stone-900 dark:text-stone-100 border border-black/[0.05] dark:border-white/[0.06] outline-none whitespace-nowrap shrink-0"
          >
            {services.map(s => (
              <option key={s.id} value={s.id}>
                {s.name} ({s.id})
              </option>
            ))}
          </select>
        </div>

        {/* Right: Controls */}
        <div className="flex flex-wrap items-center gap-2 shrink-0">
          {/* Search filter */}
          <div className="relative shrink-0">
            <Search className="w-3.5 h-3.5 text-stone-400 absolute left-2.5 top-1/2 -translate-y-1/2 shrink-0" />
            <input
              type="text"
              placeholder="Filter logs..."
              value={searchTerm}
              onChange={e => setSearchTerm(e.target.value)}
              className="pl-8 pr-2.5 py-1 rounded-xl bg-stone-50 dark:bg-stone-900 border border-black/[0.05] dark:border-white/[0.06] text-xs font-sans text-stone-800 dark:text-stone-200 outline-none w-28 sm:w-36 whitespace-nowrap"
            />
          </div>

          {/* Tail */}
          <select
            value={tail}
            onChange={e => setTail(Number(e.target.value))}
            className="rounded-xl bg-stone-100 dark:bg-stone-800 px-2 py-1 text-xs font-mono text-stone-600 dark:text-stone-300 border border-black/[0.04] dark:border-white/[0.05] outline-none whitespace-nowrap shrink-0"
          >
            <option value={50}>50 lines</option>
            <option value={150}>150 lines</option>
            <option value={300}>300 lines</option>
            <option value={500}>500 lines</option>
          </select>

          {/* Auto Poll */}
          <button
            type="button"
            onClick={() => setAutoRefresh(prev => !prev)}
            className={`flex items-center gap-1.5 px-2.5 py-1 rounded-xl text-xs font-mono transition whitespace-nowrap shrink-0 ${
              autoRefresh
                ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400'
                : 'bg-stone-100 dark:bg-stone-800 text-stone-400'
            }`}
          >
            <span
              className={`h-1.5 w-1.5 rounded-full shrink-0 ${
                autoRefresh ? 'bg-emerald-500 animate-pulse' : 'bg-stone-400'
              }`}
            />
            <span className="whitespace-nowrap">Auto</span>
          </button>

          {/* Manual Refresh */}
          <button
            type="button"
            onClick={() => fetchLogs(false)}
            disabled={isLoading}
            className="p-1.5 rounded-xl text-stone-500 hover:text-stone-900 dark:hover:text-stone-100 hover:bg-stone-100 dark:hover:bg-stone-800 transition shrink-0"
            title="Refresh logs"
          >
            <RefreshCw className={`h-3.5 w-3.5 shrink-0 ${isLoading ? 'animate-spin' : ''}`} />
          </button>

          {/* Copy */}
          <button
            type="button"
            onClick={handleCopy}
            className="p-1.5 rounded-xl text-stone-500 hover:text-stone-900 dark:hover:text-stone-100 hover:bg-stone-100 dark:hover:bg-stone-800 transition shrink-0"
            title="Copy logs"
          >
            {copied ? <Check className="h-3.5 w-3.5 text-emerald-500 shrink-0" /> : <Copy className="h-3.5 w-3.5 text-stone-500 shrink-0" />}
          </button>
        </div>
      </div>

      {/* Terminal Viewport */}
      <div className="rounded-xl bg-[#0C0D0B] border border-stone-800/80 p-3.5 font-mono text-[11px] h-[520px] overflow-y-auto shadow-inner leading-relaxed select-text">
        {filteredLines.length === 0 ? (
          <div className="h-full flex items-center justify-center text-stone-600">
            {searchTerm ? `No logs matching "${searchTerm}".` : 'No logs recorded.'}
          </div>
        ) : (
          <div className="space-y-1">
            {filteredLines.map((line, idx) => (
              <div key={idx} className="break-all flex items-start hover:bg-white/[0.03] px-1 py-0.5 rounded transition-colors">
                <span className="text-stone-600 select-none mr-2.5 font-mono text-[10px] shrink-0 w-8 text-right">
                  {idx + 1}
                </span>
                <div className="flex-1">
                  {renderColoredLine(line)}
                </div>
              </div>
            ))}
            <div ref={terminalEndRef} />
          </div>
        )}
      </div>
    </div>
  )
}
