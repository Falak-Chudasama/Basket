import React, { useState } from 'react'
import { Play, Square, RotateCw, FileText, AlertTriangle } from 'lucide-react'
import { api } from '../api/client'
import { useToast } from '../context/ToastContext'
import { playEnter, playBack } from '../lib/sound'
import type { ServiceStatus } from '../types/api'

interface ServiceRowProps {
  service: ServiceStatus
  onMutated: () => void
  onViewLogs: (serviceId: string) => void
}

/**
 * ServiceRow — Fruit Family Design System Specification (Section 5.5 List Rows)
 *
 * Anatomy: Leading status indicator, title text, category badge, trailing action buttons,
 * glass-card surface, neutral hover border, and tactile micro-transforms.
 */
export const ServiceRow: React.FC<ServiceRowProps> = ({ service, onMutated, onViewLogs }) => {
  const { success, error, info } = useToast()
  const [operating, setOperating] = useState<string | null>(null)

  const isRunning = service.is_running || service.is_healthy || service.is_listening || service.status === 'healthy'

  const handleAction = async (action: 'start' | 'end' | 'restart') => {
    if (action === 'end') {
      playBack()
    } else {
      playEnter()
    }

    try {
      setOperating(action)
      const actionLabels = { start: 'Starting', end: 'Stopping', restart: 'Restarting' }
      info(`${actionLabels[action]} ${service.name}`, 'Dispatching process...')

      let res
      if (action === 'start') res = await api.startService(service.id)
      else if (action === 'end') res = await api.endService(service.id)
      else res = await api.restartService(service.id)

      if (res.success) {
        success(service.name, res.message)
      } else {
        error(`${service.name} Failed`, res.message)
      }
      onMutated()
    } catch (err: any) {
      error(service.name, err.message)
    } finally {
      setOperating(null)
    }
  }

  const handleLogsClick = () => {
    playEnter()
    onViewLogs(service.id)
  }

  const formatUptime = (seconds: number) => {
    if (!seconds) return '0s'
    const h = Math.floor(seconds / 3600)
    const m = Math.floor((seconds % 3600) / 60)
    const s = seconds % 60
    if (h > 0) return `${h}h ${m}m`
    if (m > 0) return `${m}m ${s}s`
    return `${s}s`
  }

  return (
    <div className="glass-card flex flex-col sm:flex-row sm:items-center justify-between gap-3 rounded-2xl p-3.5 sm:px-4 shadow-soft transition-all duration-200 hover:border-stone-300 dark:hover:border-stone-700 hover:shadow-lift">
      {/* Identity & Status */}
      <div className="flex items-center gap-3 min-w-0">
        <div className="shrink-0">
          {service.status === 'healthy' ? (
            <span className="flex h-2.5 w-2.5 relative">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
              <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500" />
            </span>
          ) : service.status === 'degraded' ? (
            <AlertTriangle className="h-3.5 w-3.5 text-amber-500" />
          ) : (
            <span className="inline-flex rounded-full h-2.5 w-2.5 bg-stone-300 dark:bg-stone-700" />
          )}
        </div>

        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <h4 className="font-sans font-bold text-body text-stone-900 dark:text-stone-100 whitespace-nowrap truncate">
              {service.name}
            </h4>
            <span className="font-mono text-micro text-stone-400 dark:text-stone-500 uppercase px-1.5 py-0.5 rounded bg-stone-100 dark:bg-stone-800 whitespace-nowrap shrink-0">
              {service.category}
            </span>
          </div>
          <p className="text-caption font-sans text-stone-500 dark:text-stone-400 truncate max-w-md">
            {service.description}
          </p>
        </div>
      </div>

      {/* Metrics & Controls */}
      <div className="flex items-center justify-between sm:justify-end gap-3 shrink-0 pt-2 sm:pt-0 border-t sm:border-t-0 border-black/[0.04] dark:border-white/[0.04]">
        {/* Port & Process Stats */}
        <div className="flex items-center gap-2 font-mono text-caption text-stone-500 dark:text-stone-400 whitespace-nowrap shrink-0">
          {service.port && (
            <span className="px-2 py-0.5 rounded-lg bg-stone-100 dark:bg-stone-800/80 text-stone-700 dark:text-stone-300 whitespace-nowrap shrink-0">
              :{service.port}
            </span>
          )}

          {isRunning ? (
            <>
              {service.pid && (
                <span className="hidden md:inline text-micro text-stone-400 whitespace-nowrap shrink-0">
                  PID {service.pid}
                </span>
              )}
              {service.uptime_sec !== undefined && service.uptime_sec > 0 && (
                <span className="hidden lg:inline text-micro text-stone-400 whitespace-nowrap shrink-0">
                  {formatUptime(service.uptime_sec)}
                </span>
              )}
            </>
          ) : (
            <span className="text-micro text-stone-400 dark:text-stone-600 whitespace-nowrap shrink-0">
              Offline
            </span>
          )}
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-1 shrink-0">
          {isRunning ? (
            <>
              <button
                type="button"
                onClick={() => handleAction('restart')}
                disabled={operating !== null}
                title={`Restart ${service.name}`}
                className="focus-ring btn-interactive flex h-8 w-8 items-center justify-center rounded-xl text-stone-500 hover:bg-stone-100 dark:hover:bg-stone-800 hover:text-stone-900 dark:hover:text-stone-100 transition disabled:opacity-50 shrink-0"
              >
                <RotateCw
                  className={`h-3.5 w-3.5 shrink-0 ${operating === 'restart' ? 'animate-spin text-basket-DEFAULT dark:text-basket-200' : ''}`}
                />
              </button>
              <button
                type="button"
                onClick={() => handleAction('end')}
                disabled={operating !== null}
                className="focus-ring btn-interactive flex items-center gap-1 min-h-[36px] rounded-full px-2.5 py-1 text-caption font-semibold text-rose-600 dark:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-950/30 transition disabled:opacity-50 whitespace-nowrap shrink-0"
              >
                <Square className="h-3 w-3 fill-current shrink-0" />
                <span>Stop</span>
              </button>
            </>
          ) : (
            <button
              type="button"
              onClick={() => handleAction('start')}
              disabled={operating !== null}
              className="focus-ring btn-glass-primary flex items-center gap-1 min-h-[36px] px-3.5 py-1 text-caption font-bold transition disabled:opacity-50 whitespace-nowrap shrink-0"
            >
              <Play className="h-3 w-3 fill-current shrink-0" />
              <span>Start</span>
            </button>
          )}

          {/* View Logs Button */}
          <button
            type="button"
            onClick={handleLogsClick}
            className="focus-ring btn-interactive flex h-8 w-8 items-center justify-center rounded-xl text-stone-400 hover:text-stone-800 dark:hover:text-stone-200 hover:bg-stone-100 dark:hover:bg-stone-800 transition shrink-0"
            title={`View ${service.name} real-time logs`}
          >
            <FileText className="h-3.5 w-3.5 shrink-0" />
          </button>
        </div>
      </div>
    </div>
  )
}
