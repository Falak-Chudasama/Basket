import React, { useState } from 'react'
import { Play, Square, RotateCw, ExternalLink, Smartphone } from 'lucide-react'
import { api } from '../api/client'
import { useToast } from '../context/ToastContext'
import { playEnter, playBack } from '../lib/sound'
import type { FruitData } from '../types/api'

interface FruitCardProps {
  fruit: FruitData
  onMutated: () => void
}

/**
 * FruitCard — Fruit Family Design System Specification (Section 5.4 & 5.1)
 *
 * Anatomy: Glass card with neutral substrate, icon box, title, description,
 * status badge with indicator dot, and tactile action buttons.
 */
export const FruitCard: React.FC<FruitCardProps> = ({ fruit, onMutated }) => {
  const { success, error, info } = useToast()
  const [operating, setOperating] = useState<string | null>(null)

  const isAndroid = fruit.is_android_client
  const isRunning = fruit.is_running || fruit.api_live || (fruit.component_details && fruit.component_details.some(c => c.is_running || c.is_healthy || c.is_listening))

  const handleAction = async (action: 'start' | 'end' | 'restart') => {
    if (isAndroid) {
      playEnter()
      info(`${fruit.name} Client`, `${fruit.name} runs as a mobile Android APK on devices or emulators.`)
      return
    }

    if (action === 'end') {
      playBack()
    } else {
      playEnter()
    }

    try {
      setOperating(action)
      let res
      if (action === 'start') res = await api.startFruit(fruit.id)
      else if (action === 'end') res = await api.endFruit(fruit.id)
      else res = await api.restartFruit(fruit.id)

      if (res.success) {
        success(fruit.name, `${action.toUpperCase()} complete.`)
      } else {
        error(fruit.name, res.message || 'Operation did not finish cleanly.')
      }
      onMutated()
    } catch (err: any) {
      error(fruit.name, err.message)
    } finally {
      setOperating(null)
    }
  }

  const getPortSummary = () => {
    if (isAndroid) {
      return 'Android Client (APK) • Server origins ready'
    }
    if (!fruit.component_details || fruit.component_details.length === 0) {
      return 'Modular'
    }
    const active = fruit.component_details.filter(c => c.is_running || c.is_healthy || c.is_listening)
    if (active.length === 0) return 'Offline'
    const ports = active.map(c => `:${c.port}`).filter(p => p !== ':null' && p !== ':0')
    return `${active.length}/${fruit.component_details.length} active${ports.length > 0 ? ` (${ports.join(', ')})` : ''}`
  }

  return (
    <div className="glass-card group flex flex-col justify-between rounded-2xl p-5 shadow-soft transition-all duration-200 hover:border-stone-300 dark:hover:border-stone-700 hover:shadow-lift">
      <div>
        {/* Top Header */}
        <div className="flex items-start justify-between gap-2.5 mb-3">
          <div className="flex items-center gap-3 min-w-0">
            <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-white/60 dark:bg-stone-800/60 p-2 border border-black/[0.04] dark:border-white/[0.05] shadow-xs shrink-0">
              {fruit.icon ? (
                <img
                  src={fruit.icon}
                  alt={fruit.name}
                  className={`h-7 w-7 object-contain transition-all duration-200 ${!isRunning && !isAndroid ? 'grayscale opacity-45' : ''}`}
                />
              ) : (
                <span className="font-sans font-bold text-subtitle text-stone-700 dark:text-stone-300">
                  {fruit.name[0]}
                </span>
              )}
            </div>
            <div className="min-w-0">
              <h3 className="font-sans font-bold text-subtitle text-stone-900 dark:text-stone-100 whitespace-nowrap truncate">
                {fruit.name}
              </h3>
              <span className="text-caption text-stone-400 dark:text-stone-500 font-sans capitalize whitespace-nowrap truncate block">
                {fruit.category}
              </span>
            </div>
          </div>

          {/* Status Badge (Section 5.10) */}
          <div className="shrink-0 whitespace-nowrap">
            {isAndroid ? (
              <span className="inline-flex items-center gap-1 rounded-full bg-amber-500/10 px-2.5 py-0.5 text-caption font-semibold text-amber-700 dark:text-amber-400 whitespace-nowrap shrink-0">
                <Smartphone className="h-3 w-3 shrink-0" />
                <span className="whitespace-nowrap">Android</span>
              </span>
            ) : isRunning ? (
              <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-500/10 px-2.5 py-0.5 text-caption font-semibold text-emerald-700 dark:text-emerald-400 whitespace-nowrap shrink-0">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse shrink-0" />
                <span className="whitespace-nowrap">Active</span>
              </span>
            ) : (
              <span className="inline-flex items-center gap-1.5 rounded-full bg-stone-200/50 dark:bg-stone-800 px-2.5 py-0.5 text-caption font-semibold text-stone-500 whitespace-nowrap shrink-0">
                <span className="h-1.5 w-1.5 rounded-full bg-stone-400 shrink-0" />
                <span className="whitespace-nowrap">Stopped</span>
              </span>
            )}
          </div>
        </div>

        {/* Description */}
        <p className="text-caption font-sans text-stone-600 dark:text-stone-400 leading-relaxed line-clamp-2">
          {fruit.tagline}
        </p>

        {/* Runtime Port / Status Metadata */}
        <div className="mt-3 font-mono text-micro text-stone-400 dark:text-stone-500 whitespace-nowrap truncate">
          {getPortSummary()}
        </div>
      </div>

      {/* Footer Controls */}
      <div className="mt-5 flex items-center justify-between gap-2 border-t border-black/[0.04] dark:border-white/[0.05] pt-3">
        {/* Open App Link */}
        <div className="min-w-0 shrink-0">
          {fruit.frontend_url ? (
            <a
              href={fruit.frontend_url}
              target="_blank"
              rel="noopener noreferrer"
              onClick={() => playEnter()}
              className="focus-ring inline-flex items-center gap-1 text-caption font-semibold text-stone-600 dark:text-stone-300 hover:text-stone-900 dark:hover:text-white transition whitespace-nowrap"
            >
              <span>Open App</span>
              <ExternalLink className="h-3.5 w-3.5 shrink-0" />
            </a>
          ) : (
            <span className="text-caption text-stone-400 dark:text-stone-600 font-sans whitespace-nowrap">Local Client</span>
          )}
        </div>

        {/* Action Buttons (Section 5.1 & Touch Targets) */}
        {!isAndroid && (
          <div className="flex items-center gap-1.5 shrink-0">
            {isRunning ? (
              <>
                <button
                  type="button"
                  onClick={() => handleAction('restart')}
                  disabled={operating !== null}
                  title="Restart all services of this fruit"
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
                  <span>Stop</span>
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
                <span>Start</span>
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
