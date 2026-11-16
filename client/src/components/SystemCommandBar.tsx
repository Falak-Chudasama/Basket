import React, { useState } from 'react'
import {
  Globe,
  Play,
  Square,
  RotateCw,
  RefreshCw,
  FileCode,
  ShieldAlert,
  Loader2,
} from 'lucide-react'
import { api } from '../api/client'
import { useToast } from '../context/ToastContext'
import { playEnter, playBack } from '../lib/sound'
import type { NginxStatus, OverviewMetrics } from '../types/api'

interface SystemCommandBarProps {
  nginxData: NginxStatus | null
  metrics: OverviewMetrics | null
  onMutated: () => void
}

/**
 * SystemCommandBar — Fruit Family Design System Specification (Section 5.1 & 2.6)
 *
 * Anatomy: Glass panel (.glass-panel) housing unified Edge Proxy (Nginx) controls
 * and Master Ecosystem batch operations (Start All, Restart All, Stop All).
 */
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
    if (action === 'stop') {
      playBack()
    } else {
      playEnter()
    }

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
    playEnter()
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
    playEnter()
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
      playBack()
      setConfirmStopAll(true)
      setTimeout(() => setConfirmStopAll(false), 5000)
      return
    }
    playBack()
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
    <div className="glass-panel rounded-2xl p-4 shadow-soft transition-colors">
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        {/* Nginx Section */}
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-2 shrink-0">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-stone-100 dark:bg-stone-800 text-stone-700 dark:text-stone-300 shadow-xs shrink-0">
              <Globe className="h-4 w-4 text-basket-DEFAULT dark:text-basket-200 shrink-0" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-sans font-bold text-body text-stone-900 dark:text-stone-100 whitespace-nowrap shrink-0">
                  Nginx Edge
                </span>
                <span
                  className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-micro font-mono font-bold whitespace-nowrap shrink-0 ${
                    isNginxRunning
                      ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400'
                      : 'bg-stone-200/50 dark:bg-stone-800 text-stone-500 dark:text-stone-400'
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
              <span className="font-mono text-micro text-stone-400 dark:text-stone-500 whitespace-nowrap block">
                Ports: {p80 ? '80' : 'off'} • {p443 ? '443 (SSL)' : 'off'}
              </span>
            </div>
          </div>

          <div className="flex items-center gap-1.5 sm:ml-2 shrink-0">
            {isNginxRunning ? (
              <>
                <button
                  type="button"
                  onClick={() => handleNginxAction('reload')}
                  disabled={operating !== null}
                  title="Reload Nginx configuration (zero downtime)"
                  className="focus-ring btn-interactive flex items-center gap-1 min-h-[38px] rounded-full px-3 py-1.5 text-caption font-semibold text-stone-700 dark:text-stone-300 hover:bg-stone-100 dark:hover:bg-stone-800 transition disabled:opacity-50 whitespace-nowrap shrink-0"
                >
                  <RefreshCw
                    className={`h-3.5 w-3.5 shrink-0 ${operating === 'nginx-reload' ? 'animate-spin text-basket-DEFAULT dark:text-basket-200' : ''}`}
                  />
                  <span className="whitespace-nowrap">Reload</span>
                </button>
                <button
                  type="button"
                  onClick={() => handleNginxAction('stop')}
                  disabled={operating !== null}
                  title="Stop Nginx process"
                  className="focus-ring btn-interactive flex items-center gap-1 min-h-[38px] rounded-full px-3 py-1.5 text-caption font-semibold text-rose-600 dark:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-950/30 transition disabled:opacity-50 whitespace-nowrap shrink-0"
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
                className="focus-ring btn-glass-primary flex items-center gap-1.5 min-h-[38px] px-4 py-1.5 text-caption font-bold transition disabled:opacity-50 whitespace-nowrap shrink-0"
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
              className="focus-ring btn-interactive flex items-center gap-1 min-h-[38px] rounded-full px-3 py-1.5 text-caption font-semibold text-stone-500 hover:text-stone-800 dark:hover:text-stone-200 hover:bg-stone-100 dark:hover:bg-stone-800 transition disabled:opacity-50 whitespace-nowrap shrink-0"
            >
              <FileCode className="h-3.5 w-3.5 shrink-0" />
              <span className="hidden sm:inline whitespace-nowrap">Test Config</span>
            </button>
          </div>
        </div>

        {/* Master Control Section */}
        <div className="flex flex-wrap items-center justify-between sm:justify-end gap-3 pt-3 lg:pt-0 border-t lg:border-t-0 border-black/[0.04] dark:border-white/[0.05] shrink-0">
          {metrics && (
            <div className="flex items-center gap-1.5 text-caption font-mono text-stone-500 dark:text-stone-400 whitespace-nowrap shrink-0">
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
              className="focus-ring btn-glass-primary flex items-center gap-2 min-h-[40px] px-4 py-2 text-caption font-bold tracking-tight transition disabled:opacity-50 whitespace-nowrap shrink-0"
              title="Start all ecosystem services"
            >
              {operating === 'eco-start' ? (
                <Loader2 className="h-3.5 w-3.5 animate-spin shrink-0" />
              ) : (
                <Play className="h-3.5 w-3.5 fill-current shrink-0" />
              )}
              <span className="whitespace-nowrap">Start All</span>
            </button>

            <button
              type="button"
              onClick={handleRestartAll}
              disabled={operating !== null}
              className="focus-ring btn-glass-secondary flex items-center gap-1.5 min-h-[38px] px-4 py-1.5 text-caption font-semibold transition disabled:opacity-50 whitespace-nowrap shrink-0"
            >
              <RotateCw
                className={`h-3 w-3 shrink-0 ${operating === 'eco-restart' ? 'animate-spin text-basket-DEFAULT dark:text-basket-200' : ''}`}
              />
              <span className="whitespace-nowrap">Restart All</span>
            </button>

            {confirmStopAll ? (
              <div className="flex items-center gap-1 animate-scale-in shrink-0">
                <button
                  type="button"
                  onClick={handleStopAll}
                  disabled={operating !== null}
                  className="focus-ring btn-interactive flex items-center gap-1.5 min-h-[38px] rounded-full bg-rose-600 text-white px-3.5 py-1.5 text-caption font-bold transition hover:bg-rose-700 whitespace-nowrap shrink-0"
                >
                  <ShieldAlert className="h-3.5 w-3.5 shrink-0" />
                  <span className="whitespace-nowrap">Confirm Stop?</span>
                </button>
                <button
                  type="button"
                  onClick={() => setConfirmStopAll(false)}
                  className="btn-interactive min-h-[38px] rounded-full px-2.5 py-1.5 text-caption text-stone-500 hover:text-stone-800 dark:hover:text-stone-200 whitespace-nowrap shrink-0"
                >
                  Cancel
                </button>
              </div>
            ) : (
              <button
                type="button"
                onClick={handleStopAll}
                disabled={operating !== null}
                className="focus-ring btn-interactive flex items-center gap-1 min-h-[38px] rounded-full px-3 py-1.5 text-caption font-medium text-stone-500 hover:text-rose-600 dark:hover:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-950/20 transition disabled:opacity-50 whitespace-nowrap shrink-0"
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
