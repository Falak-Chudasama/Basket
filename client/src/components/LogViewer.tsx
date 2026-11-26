import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react'
import { RefreshCw, Copy, Check, Search, Terminal } from 'lucide-react'
import { api } from '../api/client'
import { useToast } from '../context/ToastContext'
import { playEnter, playScroll, playNotification } from '../lib/sound'
import { useShiftArrowCycle } from '../lib/keyboard'
import { getServiceIcon } from '../lib/serviceIcons'
import { ToggleSwitch } from './ToggleSwitch'
import { CustomSelect, type SelectOption } from './CustomSelect'
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

  const tsMatch = rawLine.match(/^(\[?\d{4}[-/]\d{2}[-/]\d{2}[ T]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:[+-]\d{2}:\d{2}|Z)?\]?|\d{1,2}-[A-Za-z]{3}-\d{4} \d{1,2}:\d{2}:\d{2} [AP]M|\d{1,2}\/\d{1,2}\/\d{2,4} \d{1,2}:\d{2}:\d{2})/i)

  let timestamp = ''
  let rest = rawLine
  if (tsMatch) {
    timestamp = tsMatch[0]
    rest = rawLine.slice(timestamp.length)
  }

  const levelMatch = rest.match(/(\[(?:ERROR|WARNING|WARN|NOTICE|INFO|DEBUG|SUCCESS|CRITICAL)\]|(?:ERROR|WARNING|WARN|INFO|DEBUG|SUCCESS|CRITICAL):)/i)
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
  const scrollContainerRef = useRef<HTMLDivElement>(null)
  const shouldStickToBottomRef = useRef<boolean>(true)
  const forceScrollBottomRef = useRef<boolean>(true)
  const requestSeqRef = useRef<number>(0)

  const fetchLogs = useCallback(async (silent: boolean = false) => {
    if (!selectedServiceId) return
    const reqId = ++requestSeqRef.current
    if (!silent) setIsLoading(true)
    try {
      const res = await api.getLogs(selectedServiceId, tail)
      if (reqId !== requestSeqRef.current) return
      setLines(res.lines || [])
    } catch (err: any) {
      if (reqId !== requestSeqRef.current) return
      if (!silent) error('Log Read Failed', err.message)
    } finally {
      if (reqId === requestSeqRef.current && !silent) {
        setIsLoading(false)
      }
    }
  }, [selectedServiceId, tail, error])

  useEffect(() => {
    setLines([])
    forceScrollBottomRef.current = true
    shouldStickToBottomRef.current = true
    fetchLogs(false)
  }, [fetchLogs])

  useEffect(() => {
    if (!autoRefresh) return
    const interval = setInterval(() => {
      if (document.visibilityState === 'visible') {
        fetchLogs(true)
      }
    }, 2500)
    return () => clearInterval(interval)
  }, [autoRefresh, fetchLogs])

  useEffect(() => {
    const el = scrollContainerRef.current
    if (!el) return
    if (forceScrollBottomRef.current || shouldStickToBottomRef.current) {
      el.scrollTop = el.scrollHeight
      forceScrollBottomRef.current = false
    }
  }, [lines])

  const serviceIds = useMemo(() => services.map(s => s.id), [services])

  // Shift + ArrowUp / ArrowDown cycles selected service in LogViewer
  useShiftArrowCycle({
    items: serviceIds,
    current: selectedServiceId,
    onSelect: onSelectService,
    axis: 'vertical',
    onCycle: playScroll,
  })

  const handleTerminalScroll = () => {
    const el = scrollContainerRef.current
    if (!el) return
    const distFromBottom = el.scrollHeight - el.scrollTop - el.clientHeight
    shouldStickToBottomRef.current = distFromBottom < 48
  }

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

  const serviceOptions: SelectOption[] = useMemo(() => {
    if (services.length === 0) {
      return [{ value: selectedServiceId, label: selectedServiceId }]
    }
    return services.map(s => {
      const iconPath = getServiceIcon(s)
      return {
        value: s.id,
        label: s.name,
        icon: iconPath ? (
          <img src={iconPath} alt="" className="h-4 w-4 object-contain" />
        ) : undefined,
      }
    })
  }, [services, selectedServiceId])

  const tailOptions: SelectOption[] = useMemo(
    () => [
      { value: '50', label: '50 lines' },
      { value: '150', label: '150 lines' },
      { value: '300', label: '300 lines' },
      { value: '500', label: '500 lines' },
    ],
    []
  )

  return (
    <div className="glass-card flex flex-col min-h-0 max-h-full rounded-2xl p-4 sm:p-5 shadow-soft transition-all duration-200 hover:border-stone-300 dark:hover:border-stone-700 hover:shadow-lift">
      {/* Sleek Toolbar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-3 shrink-0">
        {/* Left: Service Select */}
        <div className="flex items-center gap-2 min-w-0">
          <Terminal className="h-4 w-4 text-stone-500 shrink-0" />
          <CustomSelect
            value={selectedServiceId}
            onChange={handleServiceChange}
            options={serviceOptions}
            ariaLabel="Select service logs"
            buttonClassName="max-w-[260px] sm:max-w-[340px]"
          />
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
          <CustomSelect
            value={String(tail)}
            onChange={val => handleTailChange(Number(val))}
            options={tailOptions}
            ariaLabel="Log line count"
            buttonClassName="font-mono"
            menuClassName="right-0 left-auto"
          />

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
      <div
        ref={scrollContainerRef}
        onScroll={handleTerminalScroll}
        className="rounded-xl bg-[#0C0D0B] border border-stone-800/80 p-4 font-mono text-micro flex-1 min-h-[200px] max-h-[400px] overflow-y-auto shadow-inner leading-relaxed select-text"
      >
        {isLoading && filteredLines.length === 0 ? (
          <div className="h-full flex items-center justify-center text-stone-500">
            Loading logs...
          </div>
        ) : filteredLines.length === 0 ? (
          <div className="h-full flex items-center justify-center text-stone-600">
            {searchTerm ? `No logs matching "${searchTerm}".` : 'No logs recorded.'}
          </div>
        ) : (
          <div className="space-y-1">
            {filteredLines.map((line, idx) => (
              <div key={idx} className="break-words flex items-start hover:bg-white/[0.03] px-1 py-0.5 rounded transition-colors">
                <span className="text-stone-600 select-none mr-2.5 font-mono text-micro shrink-0 w-8 text-right">
                  {idx + 1}
                </span>
                <div className="flex-1 min-w-0">
                  {renderColoredLine(line)}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
