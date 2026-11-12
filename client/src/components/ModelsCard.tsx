import React, { useState } from 'react'
import { Sparkles, Play, Square, RotateCw } from 'lucide-react'
import { api } from '../api/client'
import { useToast } from '../context/ToastContext'
import type { ServiceStatus } from '../types/api'

interface ModelsCardProps {
  services: ServiceStatus[]
  onMutated: () => void
}

export const ModelsCard: React.FC<ModelsCardProps> = ({ services, onMutated }) => {
  const { success, error } = useToast()
  const [operating, setOperating] = useState<string | null>(null)

  // Find the 3 AI models
  const llm = services.find(s => s.id === 'llm-llama')
  const tts = services.find(s => s.id === 'tts-pocket')
  const stt = services.find(s => s.id === 'stt-qwen')

  const modelList = [
    { label: 'LLM', name: 'Qwen 3.5 CUDA', port: 10030, service: llm },
    { label: 'TTS', name: 'Pocket TTS', port: 10050, service: tts },
    { label: 'STT', name: 'Qwen3 ASR', port: 10040, service: stt },
  ]

  const activeCount = modelList.filter(m => m.service?.is_running).length
  const totalCount = modelList.length
  const isAnyRunning = activeCount > 0

  const handleAction = async (action: 'start' | 'end' | 'restart') => {
    try {
      setOperating(action)
      let res
      if (action === 'start') {
        res = await api.startModels()
      } else if (action === 'end') {
        res = await api.endModels()
      } else {
        res = await api.restartModels()
      }

      if (res.success) {
        success('AI Models Suite', `Batch ${action.toUpperCase()} completed.`)
      } else {
        error('AI Models Suite', 'Operation completed with warnings.')
      }
      onMutated()
    } catch (err: any) {
      error('AI Models Suite', err.message || 'Operation failed')
    } finally {
      setOperating(null)
    }
  }

  return (
    <div className="group flex flex-col justify-between rounded-2xl border border-basket-500/30 dark:border-basket-500/20 bg-gradient-to-b from-basket-500/[0.04] to-transparent dark:from-basket-500/[0.03] dark:bg-[#181915] p-5 shadow-soft transition-all hover:border-basket-500/50">
      <div>
        {/* Top Header - Resilient layout with no awkward word wrapping */}
        <div className="flex items-start justify-between gap-2.5 mb-3">
          <div className="flex items-center gap-3 min-w-0">
            <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-basket-500/10 text-basket-600 dark:text-basket-400 border border-basket-500/20 shrink-0">
              <Sparkles className="h-5 w-5" />
            </div>
            <div className="min-w-0">
              <h3 className="font-sans font-bold text-base text-stone-900 dark:text-stone-100 whitespace-nowrap truncate">
                AI Models
              </h3>
              <p className="text-xs text-stone-400 dark:text-stone-500 font-sans whitespace-nowrap truncate">
                LLM · TTS · STT Core
              </p>
            </div>
          </div>

          {/* Status Badge */}
          <div className="shrink-0 whitespace-nowrap">
            {activeCount === totalCount ? (
              <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-500/10 px-2.5 py-0.5 text-xs font-medium text-emerald-700 dark:text-emerald-400 whitespace-nowrap shrink-0">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse shrink-0" />
                <span className="whitespace-nowrap">{activeCount}/{totalCount} Active</span>
              </span>
            ) : activeCount > 0 ? (
              <span className="inline-flex items-center gap-1.5 rounded-full bg-amber-500/10 px-2.5 py-0.5 text-xs font-medium text-amber-700 dark:text-amber-400 whitespace-nowrap shrink-0">
                <span className="h-1.5 w-1.5 rounded-full bg-amber-500 animate-pulse shrink-0" />
                <span className="whitespace-nowrap">{activeCount}/{totalCount} Active</span>
              </span>
            ) : (
              <span className="inline-flex items-center gap-1.5 rounded-full bg-stone-100 dark:bg-stone-800 px-2.5 py-0.5 text-xs font-medium text-stone-500 whitespace-nowrap shrink-0">
                <span className="h-1.5 w-1.5 rounded-full bg-stone-400 shrink-0" />
                <span className="whitespace-nowrap">All Stopped</span>
              </span>
            )}
          </div>
        </div>

        {/* Description */}
        <p className="text-xs font-sans text-stone-600 dark:text-stone-400 leading-relaxed">
          One-click batch control to start, stop, or refresh all inference and speech models at once.
        </p>

        {/* Model instances status pills */}
        <div className="mt-3 flex flex-wrap items-center gap-1.5">
          {modelList.map(({ label, port, service }) => {
            const isRunning = service?.is_running
            return (
              <span
                key={label}
                className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-lg bg-stone-100/80 dark:bg-stone-800/80 border border-black/[0.04] dark:border-white/[0.05] text-[11px] font-mono text-stone-600 dark:text-stone-300 whitespace-nowrap shrink-0"
              >
                <span
                  className={`h-1.5 w-1.5 rounded-full shrink-0 ${
                    isRunning ? 'bg-emerald-500 animate-pulse' : 'bg-stone-400'
                  }`}
                />
                <span className="font-semibold">{label}</span>
                <span className="text-stone-400 text-[10px]">:{port}</span>
              </span>
            )
          })}
        </div>
      </div>

      {/* Footer Controls - Clean responsive button bar with zero text wrapping */}
      <div className="mt-5 flex items-center justify-between gap-2 border-t border-black/[0.04] dark:border-white/[0.05] pt-3">
        <span className="text-xs text-stone-400 dark:text-stone-500 font-sans whitespace-nowrap truncate min-w-0">
          Models Suite
        </span>

        {/* Action Buttons with strict whitespace-nowrap shrink-0 */}
        <div className="flex items-center justify-end gap-1.5 shrink-0">
          {isAnyRunning && (
            <>
              <button
                type="button"
                onClick={() => handleAction('restart')}
                disabled={operating !== null}
                title="Refresh and restart all models"
                className="focus-ring flex items-center gap-1 rounded-lg px-2.5 py-1 text-xs font-medium text-stone-600 dark:text-stone-300 hover:bg-stone-100 dark:hover:bg-stone-800 transition disabled:opacity-50 whitespace-nowrap shrink-0"
              >
                <RotateCw
                  className={`h-3 w-3 shrink-0 ${operating === 'restart' ? 'animate-spin text-basket-500' : ''}`}
                />
                <span className="whitespace-nowrap">Refresh</span>
              </button>
              <button
                type="button"
                onClick={() => handleAction('end')}
                disabled={operating !== null}
                title="Stop all AI models at once"
                className="focus-ring flex items-center gap-1 rounded-lg px-2.5 py-1 text-xs font-medium text-rose-600 dark:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-950/30 transition disabled:opacity-50 whitespace-nowrap shrink-0"
              >
                <Square className="h-2.5 w-2.5 fill-current shrink-0" />
                <span className="whitespace-nowrap">Stop All</span>
              </button>
            </>
          )}

          {activeCount < totalCount && (
            <button
              type="button"
              onClick={() => handleAction('start')}
              disabled={operating !== null}
              title="Start all AI models"
              className="focus-ring flex items-center gap-1 rounded-lg bg-stone-900 text-white dark:bg-stone-100 dark:text-stone-900 px-3 py-1 text-xs font-semibold transition hover:opacity-90 disabled:opacity-50 whitespace-nowrap shrink-0"
            >
              <Play className="h-2.5 w-2.5 fill-current shrink-0" />
              <span className="whitespace-nowrap">Start All</span>
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
