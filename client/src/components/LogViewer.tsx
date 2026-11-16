import React, { useState, useEffect, useRef } from 'react'
import { RefreshCw, Copy, Check, Search, Terminal } from 'lucide-react'
import { api } from '../api/client'
import { useToast } from '../context/ToastContext'
import { playEnter, playScroll, playNotification } from '../lib/sound'
import { ToggleSwitch } from './ToggleSwitch'
import type { ServiceStatus } from '../types/api'

interface LogViewerProps {
  services: ServiceStatus[]
  selectedServiceId: string
  onSelectService: (id: string) => void
}

const renderColoredLine = (rawLine: string) => {
  if (/^[=\-_]{8,}$/.test(rawLine.trim())) {
    return <span className="text-stone-600 font-bold">{rawLine}</span>
  }

  const tsMatch = rawLine.match(/^(\[?\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:[+-]\d{2}:\d{2}|Z)?\]?|\d{1,2}-[A-Za-z]{3}-\d{4} \d{1,2}:\d{2}:\d{2} [AP]M|\d{1,2}\/\d{1,2}\/\d{2,4} \d{1,2}:\d{2}:\d{2})/i)

  let timestamp = ''
  let rest = rawLine
  if (tsMatch) {
    timestamp = tsMatch[0]
    rest = rawLine.slice(timestamp.length)
  }

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

  const highlightContent = (text: string) => {
    const regex = /(https?:\/\/[^\s]+|wss?:\/\/[^\s]+|\b(?:GET|POST|PUT|DELETE|PATCH|OPTIONS|HEAD)\b|\b(?:200 OK|HTTP\/1\.[01] 200|200|201|204|400|401|403|404|422|500|502|503)\b|\b(?:listening at|listening on|connected|startup complete|ready in|WiredTiger|MongoDB starting|Application startup|Uvicorn running|STOPPED|STARTING)\b|\b(?:Traceback|Exception|Error|failed|invalid_grant)\b)/gi

    const parts = text.split(regex)
    return parts.map((part, i) => {
      if (!part) return null
      const lower = part.toLowerCase()

      if (lower.startsWith('http://') || lower.startsWith('https://') || lower.startsWith('ws://') || lower.startsWith('wss://')) {
        return <span key={i} className="text-cyan-400 underline decoration-cyan-500/40">{part}</span>
      }
      if (/^(GET|POST|PUT|DELETE|PATCH|OPTIONS|HEAD)$/i.test(part)) {
        return <span key={i} className="text-indigo-400 font-bold">{part}</span>
      }
      if (part === '200 OK' || part.includes('200') || part === '201') {
        return <span key={i} className="text-emerald-400 font-bold">{part}</span>
      }
      if (/^(400|401|403|404|422)$/.test(part)) {
        return <span key={i} className="text-amber-400 font-bold">{part}</span>
      }
      if (/^(500|502|503)$/.test(part)) {
        return <span key={i} className="text-rose-400 font-bold">{part}</span>
      }
      if (lower.includes('listening') || lower.includes('connected') || lower.includes('ready in') || lower.includes('startup') || lower.includes('starting')) {
        return <span key={i} className="text-emerald-300 font-medium">{part}</span>
      }
      if (lower.includes('error') || lower.includes('traceback') || lower.includes('exception') || lower.includes('failed') || lower.includes('stopped') || lower.includes('invalid_grant')) {
        return <span key={i} className="text-rose-400 font-semibold">{part}</span>
      }

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

/**
 * LogViewer — Fruit Family Design System Specification (Section 5.3 & 5.4)
 *
 * Terminal console featuring real-time stdout/stderr stream, Azeret Mono font,
 * Search input (Section 5.3), ToggleSwitch (Section 5.2), and glass-card container.
 */
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
    playNotification()
    success('Copied', 'Log lines copied to clipboard.')
    setTimeout(() => setCopied(false), 2000)
  }

  const handleServiceChange = (id: string) => {
    playScroll()
    onSelectService(id)
  }

  const handleTailChange = (val: number) => {
    playScroll()
    setTail(val)
  }

  const handleManualRefresh = () => {
    playEnter()
    fetchLogs(false)
  }

  const filteredLines = searchTerm
    ? lines.filter(line => line.toLowerCase().includes(searchTerm.toLowerCase()))
    : lines

  return (
    <div className="glass-card rounded-2xl p-4 sm:p-5 shadow-soft transition-all duration-200 hover:border-stone-300 dark:hover:border-stone-700 hover:shadow-lift">
      {/* Sleek Toolbar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
        {/* Left: Service Select */}
        <div className="flex items-center gap-2 shrink-0">
          <Terminal className="h-4 w-4 text-stone-500 shrink-0" />
          <select
            value={selectedServiceId}
            onChange={e => handleServiceChange(e.target.value)}
            className="focus-ring rounded-xl bg-stone-100 dark:bg-stone-800/80 px-3 py-1.5 text-caption font-semibold font-sans text-stone-900 dark:text-stone-100 border border-black/[0.05] dark:border-white/[0.06] outline-none whitespace-nowrap shrink-0"
          >
            {services.map(s => (
              <option key={s.id} value={s.id}>
                {s.name} ({s.id})
              </option>
            ))}
          </select>
        </div>

        {/* Right: Search, Tail, Auto-Toggle, Actions */}
        <div className="flex flex-wrap items-center gap-2 shrink-0">
          {/* Search filter input (Section 5.3 Text Inputs) */}
          <div className="relative shrink-0">
            <Search className="w-3.5 h-3.5 text-stone-400 absolute left-3 top-1/2 -translate-y-1/2 shrink-0" />
            <input
              type="text"
              placeholder="Filter logs..."
              value={searchTerm}
              onChange={e => setSearchTerm(e.target.value)}
              className="focus-ring pl-8 pr-3 py-1.5 rounded-xl bg-stone-100/80 dark:bg-stone-900/80 border border-black/[0.08] dark:border-white/[0.10] text-caption font-sans text-stone-900 dark:text-stone-100 outline-none w-32 sm:w-44 whitespace-nowrap"
            />
          </div>

          {/* Tail Dropdown */}
          <select
            value={tail}
            onChange={e => handleTailChange(Number(e.target.value))}
            className="focus-ring rounded-xl bg-stone-100 dark:bg-stone-800 px-2.5 py-1.5 text-caption font-mono text-stone-600 dark:text-stone-300 border border-black/[0.04] dark:border-white/[0.05] outline-none whitespace-nowrap shrink-0"
          >
            <option value={50}>50 lines</option>
            <option value={150}>150 lines</option>
            <option value={300}>300 lines</option>
            <option value={500}>500 lines</option>
          </select>

          {/* Auto Refresh Switch (Section 5.2) */}
          <div className="flex items-center gap-1.5 pl-1 shrink-0">
            <ToggleSwitch
              checked={autoRefresh}
              onChange={setAutoRefresh}
              id="log-auto-refresh"
            />
            <span className="text-micro font-mono text-stone-500 dark:text-stone-400 select-none">
              Auto
            </span>
          </div>

          {/* Manual Refresh */}
          <button
            type="button"
            onClick={handleManualRefresh}
            disabled={isLoading}
            className="focus-ring btn-interactive min-w-[36px] min-h-[36px] flex items-center justify-center rounded-xl text-stone-500 hover:text-stone-900 dark:hover:text-stone-100 hover:bg-stone-100 dark:hover:bg-stone-800 transition shrink-0"
            title="Refresh logs"
          >
            <RefreshCw className={`h-3.5 w-3.5 shrink-0 ${isLoading ? 'animate-spin text-basket-DEFAULT dark:text-basket-200' : ''}`} />
          </button>

          {/* Copy */}
          <button
            type="button"
            onClick={handleCopy}
            className="focus-ring btn-interactive min-w-[36px] min-h-[36px] flex items-center justify-center rounded-xl text-stone-500 hover:text-stone-900 dark:hover:text-stone-100 hover:bg-stone-100 dark:hover:bg-stone-800 transition shrink-0"
            title="Copy logs"
          >
            {copied ? <Check className="h-3.5 w-3.5 text-emerald-500 shrink-0" /> : <Copy className="h-3.5 w-3.5 text-stone-500 shrink-0" />}
          </button>
        </div>
      </div>

      {/* Terminal Viewport */}
      <div className="rounded-xl bg-[#0C0D0B] border border-stone-800/80 p-4 font-mono text-micro h-[520px] overflow-y-auto shadow-inner leading-relaxed select-text">
        {filteredLines.length === 0 ? (
          <div className="h-full flex items-center justify-center text-stone-600">
            {searchTerm ? `No logs matching "${searchTerm}".` : 'No logs recorded.'}
          </div>
        ) : (
          <div className="space-y-1">
            {filteredLines.map((line, idx) => (
              <div key={idx} className="break-all flex items-start hover:bg-white/[0.03] px-1 py-0.5 rounded transition-colors">
                <span className="text-stone-600 select-none mr-2.5 font-mono text-micro shrink-0 w-8 text-right">
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
