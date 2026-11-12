import React, { useState } from 'react'
import { Play, Square, RotateCw, ExternalLink, Smartphone } from 'lucide-react'
import { api } from '../api/client'
import { useToast } from '../context/ToastContext'
import type { FruitData } from '../types/api'

interface FruitCardProps {
  fruit: FruitData
  onMutated: () => void
}

export const FruitCard: React.FC<FruitCardProps> = ({ fruit, onMutated }) => {
  const { success, error, info } = useToast()
  const [operating, setOperating] = useState<string | null>(null)

  const isAndroid = fruit.is_android_client || fruit.id === 'lemon'
  const isRunning = fruit.is_running

  const handleAction = async (action: 'start' | 'end' | 'restart') => {
    if (isAndroid) {
      info('Lemon Android Client', 'Lemon runs as a mobile Android APK on devices or emulators.')
      return
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

  // Active ports or components summary
  const getPortSummary = () => {
    if (isAndroid) {
      return 'Android Client (APK) • Server origins ready'
    }
    if (!fruit.component_details || fruit.component_details.length === 0) {
      return 'Modular components'
    }
    const active = fruit.component_details.filter(c => c.is_running)
    if (active.length === 0) return 'All components offline'
    const ports = active.map(c => `:${c.port}`).filter(p => p !== ':null' && p !== ':0')
    return `${active.length}/${fruit.component_details.length} active${ports.length > 0 ? ` (${ports.join(', ')})` : ''}`
  }

  return (
    <div className="group flex flex-col justify-between rounded-2xl border border-black/[0.06] dark:border-white/[0.08] bg-white dark:bg-[#181915] p-5 shadow-soft transition-all hover:border-black/20 dark:hover:border-white/20">
      <div>
        {/* Top Header - Resilient flex layout */}
        <div className="flex items-start justify-between gap-2.5 mb-3">
          <div className="flex items-center gap-3 min-w-0">
            <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-stone-100 dark:bg-stone-800 p-2 border border-black/[0.04] dark:border-white/[0.05] shrink-0">
              {fruit.icon ? (
                <img src={fruit.icon} alt={fruit.name} className="h-7 w-7 object-contain" />
              ) : (
                <span className="font-sans font-bold text-base text-stone-700 dark:text-stone-300">
                  {fruit.name[0]}
                </span>
              )}
            </div>
            <div className="min-w-0">
              <h3 className="font-sans font-bold text-base text-stone-900 dark:text-stone-100 whitespace-nowrap truncate">
                {fruit.name}
              </h3>
              <span className="text-xs text-stone-400 dark:text-stone-500 font-sans capitalize whitespace-nowrap truncate block">
                {fruit.category}
              </span>
            </div>
          </div>

          {/* Status Badge */}
          <div className="shrink-0 whitespace-nowrap">
            {isAndroid ? (
              <span className="inline-flex items-center gap-1 rounded-full bg-amber-500/10 px-2.5 py-0.5 text-xs font-medium text-amber-700 dark:text-amber-400 whitespace-nowrap shrink-0">
                <Smartphone className="h-3 w-3 shrink-0" />
                <span className="whitespace-nowrap">Android</span>
              </span>
            ) : isRunning ? (
              <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-500/10 px-2.5 py-0.5 text-xs font-medium text-emerald-700 dark:text-emerald-400 whitespace-nowrap shrink-0">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse shrink-0" />
                <span className="whitespace-nowrap">Active</span>
              </span>
            ) : (
              <span className="inline-flex items-center gap-1.5 rounded-full bg-stone-100 dark:bg-stone-800 px-2.5 py-0.5 text-xs font-medium text-stone-500 whitespace-nowrap shrink-0">
                <span className="h-1.5 w-1.5 rounded-full bg-stone-400 shrink-0" />
                <span className="whitespace-nowrap">Stopped</span>
              </span>
            )}
          </div>
        </div>

        {/* Concise Description */}
        <p className="text-xs font-sans text-stone-600 dark:text-stone-400 leading-relaxed line-clamp-2">
          {fruit.tagline}
        </p>

        {/* Runtime Port / Status Metadata */}
        <div className="mt-3 font-mono text-[11px] text-stone-400 dark:text-stone-500 whitespace-nowrap truncate">
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
              className="focus-ring inline-flex items-center gap-1 text-xs font-semibold text-stone-600 dark:text-stone-300 hover:text-stone-900 dark:hover:text-white transition whitespace-nowrap"
            >
              <span>Open App</span>
              <ExternalLink className="h-3 w-3 shrink-0" />
            </a>
          ) : (
            <span className="text-xs text-stone-400 dark:text-stone-600 font-sans whitespace-nowrap">Local Client</span>
          )}
        </div>

        {/* Actions with strict whitespace-nowrap */}
        {!isAndroid && (
          <div className="flex items-center gap-1 shrink-0">
            {isRunning ? (
              <>
                <button
                  type="button"
                  onClick={() => handleAction('restart')}
                  disabled={operating !== null}
                  title="Restart all services of this fruit"
                  className="focus-ring flex h-7 w-7 items-center justify-center rounded-lg text-stone-500 hover:bg-stone-100 dark:hover:bg-stone-800 hover:text-stone-900 dark:hover:text-stone-100 transition disabled:opacity-50 shrink-0"
                >
                  <RotateCw
                    className={`h-3 w-3 shrink-0 ${operating === 'restart' ? 'animate-spin text-basket-500' : ''}`}
                  />
                </button>
                <button
                  type="button"
                  onClick={() => handleAction('end')}
                  disabled={operating !== null}
                  className="focus-ring flex items-center gap-1 rounded-lg px-2.5 py-1 text-xs font-medium text-rose-600 dark:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-950/30 transition disabled:opacity-50 whitespace-nowrap shrink-0"
                >
                  <Square className="h-2.5 w-2.5 fill-current shrink-0" />
                  <span>Stop</span>
                </button>
              </>
            ) : (
              <button
                type="button"
                onClick={() => handleAction('start')}
                disabled={operating !== null}
                className="focus-ring flex items-center gap-1 rounded-lg bg-stone-900 text-white dark:bg-stone-100 dark:text-stone-900 px-3 py-1 text-xs font-semibold transition hover:opacity-90 disabled:opacity-50 whitespace-nowrap shrink-0"
              >
                <Play className="h-2.5 w-2.5 fill-current shrink-0" />
                <span>Start</span>
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
