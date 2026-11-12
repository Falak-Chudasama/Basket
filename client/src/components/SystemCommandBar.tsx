import React, { useState } from 'react'
import {
  Globe,
  Play,
  Square,
  RotateCw,
  RefreshCw,
  FileCode,
  ShieldAlert,
  CheckCircle2,
} from 'lucide-react'
import { api } from '../api/client'
import { useToast } from '../context/ToastContext'
import type { NginxStatus, OverviewMetrics } from '../types/api'

interface SystemCommandBarProps {
  nginxData: NginxStatus | null
  metrics: OverviewMetrics | null
  onMutated: () => void
}

export const SystemCommandBar: React.FC<SystemCommandBarProps> = ({
  nginxData,
  metrics,
  onMutated,
}) => {
  const { success, error, info } = useToast()
  const [operating, setOperating] = useState<string | null>(null)
  const [confirmStopAll, setConfirmStopAll] = useState(false)

  const isNginxRunning = nginxData?.status.is_running ?? false
  const p80 = nginxData?.listening_80 ?? false
  const p443 = nginxData?.listening_443 ?? false

  // Nginx Actions
  const handleNginxAction = async (action: 'start' | 'stop' | 'reload' | 'validate') => {
    try {
      setOperating(`nginx-${action}`)
      if (action === 'start') {
        const res = await api.startService('nginx')
        if (res.success) success('Nginx Started', res.message)
        else error('Start Failed', res.message)
      } else if (action === 'stop') {
        const res = await api.endService('nginx')
        if (res.success) success('Nginx Stopped', res.message)
        else error('Stop Failed', res.message)
      } else if (action === 'reload') {
        const res = await api.reloadNginx()
        if (res.success) success('Nginx Reloaded', res.message)
        else error('Reload Failed', res.message)
      } else if (action === 'validate') {
        const res = await api.validateNginx()
        if (res.valid) {
          success('Config Valid', 'nginx -t passed with exit code 0.')
        } else {
          error('Syntax Error', res.stderr || 'nginx -t failed. Check nginx.conf.')
        }
      }
      onMutated()
    } catch (err: any) {
      error('Nginx Error', err.message)
    } finally {
      setOperating(null)
    }
  }

  // Master Ecosystem Actions
  const handleStartAll = async () => {
    try {
      setOperating('eco-start')
      info('Starting Ecosystem', 'Launching services in dependency order...')
      const res = await api.startAllServices()
      if (res.success) success('All Services Online', 'Ecosystem started.')
      else error('Startup Incomplete', 'Some services did not respond.')
      onMutated()
    } catch (err: any) {
      error('Start All Failed', err.message)
    } finally {
      setOperating(null)
    }
  }

  const handleRestartAll = async () => {
    try {
      setOperating('eco-restart')
      info('Restarting Ecosystem', 'Refreshing all services...')
      const res = await api.restartAllServices()
      if (res.success) success('Ecosystem Refreshed', 'All services restarted.')
      else error('Restart Incomplete', 'Some services failed to restart.')
      onMutated()
    } catch (err: any) {
      error('Restart Failed', err.message)
    } finally {
      setOperating(null)
    }
  }

  const handleStopAll = async () => {
    if (!confirmStopAll) {
      setConfirmStopAll(true)
      setTimeout(() => setConfirmStopAll(false), 5000)
      return
    }
    try {
      setOperating('eco-stop')
      setConfirmStopAll(false)
      const res = await api.endAllServices()
      if (res.success) success('Ecosystem Terminated', 'All services stopped.')
      else error('Stop Incomplete', 'Some services did not stop cleanly.')
      onMutated()
    } catch (err: any) {
      error('Stop All Failed', err.message)
    } finally {
      setOperating(null)
    }
  }

  return (
    <div className="rounded-2xl border border-black/[0.06] dark:border-white/[0.08] bg-white dark:bg-[#181915] p-4 shadow-soft transition-colors">
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        {/* Nginx Section */}
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-2 shrink-0">
            <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-stone-100 dark:bg-stone-800 text-stone-700 dark:text-stone-300 shrink-0">
              <Globe className="h-4 w-4 text-basket-500 shrink-0" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-sans font-bold text-sm text-stone-900 dark:text-stone-100 whitespace-nowrap shrink-0">
                  Nginx Edge
                </span>
                <span
                  className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-mono font-semibold whitespace-nowrap shrink-0 ${
                    isNginxRunning
                      ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400'
                      : 'bg-stone-100 dark:bg-stone-800 text-stone-500 dark:text-stone-400'
                  }`}
                >
                  <span
                    className={`h-1.5 w-1.5 rounded-full shrink-0 ${
                      isNginxRunning ? 'bg-emerald-500 animate-pulse' : 'bg-stone-400'
                    }`}
                  />
                  <span className="whitespace-nowrap">{isNginxRunning ? 'Active' : 'Stopped'}</span>
                </span>
              </div>
              <span className="font-mono text-[11px] text-stone-400 dark:text-stone-500 whitespace-nowrap block">
                Ports: {p80 ? '80' : 'off'} • {p443 ? '443 (SSL)' : 'off'}
              </span>
            </div>
          </div>

          <div className="flex items-center gap-1 sm:ml-2 shrink-0">
            {isNginxRunning ? (
              <>
                <button
                  type="button"
                  onClick={() => handleNginxAction('reload')}
                  disabled={operating !== null}
                  title="Reload Nginx configuration (zero downtime)"
                  className="focus-ring flex items-center gap-1 rounded-xl px-2.5 py-1.5 text-xs font-medium text-stone-700 dark:text-stone-300 hover:bg-stone-100 dark:hover:bg-stone-800 transition disabled:opacity-50 whitespace-nowrap shrink-0"
                >
                  <RefreshCw
                    className={`h-3.5 w-3.5 shrink-0 ${operating === 'nginx-reload' ? 'animate-spin text-basket-500' : ''}`}
                  />
                  <span className="whitespace-nowrap">Reload</span>
                </button>
                <button
                  type="button"
                  onClick={() => handleNginxAction('stop')}
                  disabled={operating !== null}
                  title="Stop Nginx process"
                  className="focus-ring flex items-center gap-1 rounded-xl px-2.5 py-1.5 text-xs font-medium text-rose-600 dark:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-950/30 transition disabled:opacity-50 whitespace-nowrap shrink-0"
                >
                  <Square className="h-3 w-3 fill-current shrink-0" />
                  <span className="whitespace-nowrap">Stop</span>
                </button>
              </>
            ) : (
              <button
                type="button"
                onClick={() => handleNginxAction('start')}
                disabled={operating !== null}
                className="focus-ring flex items-center gap-1 rounded-xl bg-stone-900 text-white dark:bg-stone-100 dark:text-stone-900 px-3 py-1.5 text-xs font-semibold transition hover:opacity-90 disabled:opacity-50 whitespace-nowrap shrink-0"
              >
                <Play className="h-3 w-3 fill-current shrink-0" />
                <span className="whitespace-nowrap">Start</span>
              </button>
            )}

            <button
              type="button"
              onClick={() => handleNginxAction('validate')}
              disabled={operating !== null}
              title="Validate Nginx configuration syntax (nginx -t)"
              className="focus-ring flex items-center gap-1 rounded-xl px-2.5 py-1.5 text-xs font-medium text-stone-500 hover:text-stone-800 dark:hover:text-stone-200 hover:bg-stone-100 dark:hover:bg-stone-800 transition disabled:opacity-50 whitespace-nowrap shrink-0"
            >
              <FileCode className="h-3.5 w-3.5 shrink-0" />
              <span className="hidden sm:inline whitespace-nowrap">Test Config</span>
            </button>
          </div>
        </div>

        {/* Master Control Section */}
        <div className="flex flex-wrap items-center justify-between sm:justify-end gap-3 pt-3 lg:pt-0 border-t lg:border-t-0 border-black/[0.04] dark:border-white/[0.05] shrink-0">
          {metrics && (
            <div className="flex items-center gap-1.5 text-xs font-mono text-stone-500 dark:text-stone-400 whitespace-nowrap shrink-0">
              <span className="font-semibold text-stone-900 dark:text-stone-100">
                {metrics.running_services}/{metrics.total_services}
              </span>
              <span>Services</span>
              <span className="text-stone-300 dark:text-stone-700">•</span>
              <span className="font-semibold text-stone-900 dark:text-stone-100">
                {metrics.live_routes}/{metrics.total_routes}
              </span>
              <span>Routes</span>
            </div>
          )}

          <div className="flex items-center gap-1.5 shrink-0">
            <button
              type="button"
              onClick={handleStartAll}
              disabled={operating !== null}
              className="focus-ring flex items-center gap-1 rounded-xl bg-stone-900 text-white dark:bg-stone-100 dark:text-stone-900 px-3 py-1.5 text-xs font-semibold transition hover:opacity-90 disabled:opacity-50 whitespace-nowrap shrink-0"
            >
              <Play
                className={`h-3 w-3 fill-current shrink-0 ${operating === 'eco-start' ? 'animate-spin' : ''}`}
              />
              <span className="whitespace-nowrap">Start All</span>
            </button>

            <button
              type="button"
              onClick={handleRestartAll}
              disabled={operating !== null}
              className="focus-ring flex items-center gap-1 rounded-xl border border-black/[0.08] dark:border-white/[0.08] bg-white dark:bg-[#181915] text-stone-800 dark:text-stone-200 px-3 py-1.5 text-xs font-semibold hover:bg-stone-50 dark:hover:bg-stone-800 transition disabled:opacity-50 whitespace-nowrap shrink-0"
            >
              <RotateCw
                className={`h-3 w-3 shrink-0 ${operating === 'eco-restart' ? 'animate-spin text-basket-500' : ''}`}
              />
              <span className="whitespace-nowrap">Restart All</span>
            </button>

            {confirmStopAll ? (
              <div className="flex items-center gap-1 animate-scale-in shrink-0">
                <button
                  type="button"
                  onClick={handleStopAll}
                  disabled={operating !== null}
                  className="focus-ring flex items-center gap-1 rounded-xl bg-rose-600 text-white px-3 py-1.5 text-xs font-bold transition hover:bg-rose-700 whitespace-nowrap shrink-0"
                >
                  <ShieldAlert className="h-3.5 w-3.5 shrink-0" />
                  <span className="whitespace-nowrap">Confirm Stop?</span>
                </button>
                <button
                  type="button"
                  onClick={() => setConfirmStopAll(false)}
                  className="rounded-xl px-2 py-1.5 text-xs text-stone-500 hover:text-stone-800 dark:hover:text-stone-200 whitespace-nowrap shrink-0"
                >
                  Cancel
                </button>
              </div>
            ) : (
              <button
                type="button"
                onClick={handleStopAll}
                disabled={operating !== null}
                className="focus-ring flex items-center gap-1 rounded-xl px-3 py-1.5 text-xs font-medium text-stone-500 hover:text-rose-600 dark:hover:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-950/20 transition disabled:opacity-50 whitespace-nowrap shrink-0"
              >
                <Square className="h-3 w-3 fill-current shrink-0" />
                <span className="whitespace-nowrap">Stop All</span>
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

