import React, { useState } from 'react'
import { Sparkles, Play, Square, RotateCw } from 'lucide-react'
import { api } from '../api/client'
import { useToast } from '../context/ToastContext'
import { playEnter, playBack } from '../lib/sound'
import type { ServiceStatus } from '../types/api'

interface ModelsCardProps {
  services: ServiceStatus[]
  onMutated: () => void
}

/**
 * ModelsCard — Fruit Family Design System Specification (Section 5.4 & 3.5)
 *
 * Anatomy: Glass card with neutral substrate (cards remain neutral per Section 3.5 Accent Budget).
 * AI models routine batch control: LLM (llama.cpp / Qwen), TTS (Pocket TTS), STT (Qwen3 ASR).
 */
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
    if (action === 'end') {
      playBack()
    } else {
      playEnter()
    }

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
    <div className="glass-card group flex flex-col justify-between rounded-2xl p-5 shadow-soft transition-all duration-200 hover:border-stone-300 dark:hover:border-stone-700 hover:shadow-lift">
      <div>
        {/* Top Header */}
        <div className="flex items-start justify-between gap-2.5 mb-3">
          <div className="flex items-center gap-3 min-w-0">
            <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-stone-100 dark:bg-stone-800 text-stone-700 dark:text-stone-300 border border-black/[0.04] dark:border-white/[0.05] shadow-xs shrink-0">
              <Sparkles className="h-5 w-5 text-basket-DEFAULT dark:text-basket-200" />
            </div>
            <div className="min-w-0">
              <h3 className="font-sans font-bold text-subtitle text-stone-900 dark:text-stone-100 whitespace-nowrap truncate">
                AI Models
              </h3>
              <p className="text-caption text-stone-400 dark:text-stone-500 font-sans whitespace-nowrap truncate">
                LLM · TTS · STT Suite
              </p>
            </div>
          </div>

          {/* Status Badge */}
          <div className="shrink-0 whitespace-nowrap">
            {activeCount === totalCount ? (
              <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-500/10 px-2.5 py-0.5 text-caption font-semibold text-emerald-700 dark:text-emerald-400 whitespace-nowrap shrink-0">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse shrink-0" />
                <span className="whitespace-nowrap">{activeCount}/{totalCount} Active</span>
              </span>
            ) : activeCount > 0 ? (
              <span className="inline-flex items-center gap-1.5 rounded-full bg-amber-500/10 px-2.5 py-0.5 text-caption font-semibold text-amber-700 dark:text-amber-400 whitespace-nowrap shrink-0">
                <span className="h-1.5 w-1.5 rounded-full bg-amber-500 animate-pulse shrink-0" />
                <span className="whitespace-nowrap">{activeCount}/{totalCount} Active</span>
              </span>
            ) : (
              <span className="inline-flex items-center gap-1.5 rounded-full bg-stone-200/50 dark:bg-stone-800 px-2.5 py-0.5 text-caption font-semibold text-stone-500 whitespace-nowrap shrink-0">
                <span className="h-1.5 w-1.5 rounded-full bg-stone-400 shrink-0" />
                <span className="whitespace-nowrap">All Stopped</span>
              </span>
            )}
          </div>
        </div>

        {/* Description */}
        <p className="text-caption font-sans text-stone-600 dark:text-stone-400 leading-relaxed">
          One-click batch control to start, stop, or refresh inference, speech recognition, and synthesis engines in unified sequence.
        </p>

        {/* Model Chips */}
        <div className="mt-3 flex flex-wrap gap-1.5">
          {modelList.map(m => {
            const isRunning = m.service?.is_running
            return (
              <div
                key={m.label}
                className="flex items-center gap-1.5 rounded-lg bg-black/[0.03] dark:bg-white/[0.04] px-2 py-1 text-micro font-mono border border-black/[0.03] dark:border-white/[0.04]"
              >
                <span
                  className={`h-1.5 w-1.5 rounded-full shrink-0 ${
                    isRunning ? 'bg-emerald-500' : 'bg-stone-400'
                  }`}
                />
                <span className="font-bold text-stone-700 dark:text-stone-300 font-sans">{m.label}</span>
                <span className="text-stone-400 dark:text-stone-500">:{m.port}</span>
              </div>
            )
          })}
        </div>
      </div>

      {/* Footer Controls */}
      <div className="mt-5 flex items-center justify-between gap-2 border-t border-black/[0.04] dark:border-white/[0.05] pt-3">
        <span className="text-caption font-mono text-stone-400 dark:text-stone-500 whitespace-nowrap">
          {isAnyRunning ? `${activeCount} online` : 'Idle'}
        </span>

        <div className="flex items-center gap-1.5 shrink-0">
          {isAnyRunning ? (
            <>
              <button
                type="button"
                onClick={() => handleAction('restart')}
                disabled={operating !== null}
                title="Restart all 3 AI models"
                className="focus-ring btn-interactive flex h-9 w-9 items-center justify-center rounded-xl text-stone-500 hover:bg-stone-100 dark:hover:bg-stone-800 hover:text-stone-900 dark:hover:text-stone-100 transition disabled:opacity-50 shrink-0"
              >
                <RotateCw
                  className={`h-3.5 w-3.5 shrink-0 ${operating === 'restart' ? 'animate-spin text-basket-DEFAULT dark:text-basket-200' : ''}`}
                />
              </button>
              <button
                type="button"
                onClick={() => handleAction('end')}
                disabled={operating !== null}
                className="focus-ring btn-interactive flex items-center gap-1 min-h-[38px] rounded-full px-3 py-1.5 text-caption font-semibold text-rose-600 dark:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-950/30 transition disabled:opacity-50 whitespace-nowrap shrink-0"
              >
                <Square className="h-3 w-3 fill-current shrink-0" />
                <span>Stop All</span>
              </button>
            </>
          ) : (
            <button
              type="button"
              onClick={() => handleAction('start')}
              disabled={operating !== null}
              className="focus-ring btn-glass-primary flex items-center gap-1.5 min-h-[38px] px-4 py-1.5 text-caption font-bold transition disabled:opacity-50 whitespace-nowrap shrink-0"
            >
              <Play className="h-3 w-3 fill-current shrink-0" />
              <span>Start Suite</span>
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
