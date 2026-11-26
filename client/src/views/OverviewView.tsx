import React from 'react'
import { TelemetryHUD } from '../components/TelemetryHUD'
import { SystemCommandBar } from '../components/SystemCommandBar'
import { FruitCard } from '../components/FruitCard'
import { ModelsCard } from '../components/ModelsCard'
import type { OverviewResponse, NginxStatus, SystemTelemetry } from '../types/api'

interface OverviewViewProps {
  overview: OverviewResponse | null
  telemetry: SystemTelemetry | null
  nginxData: NginxStatus | null
  onMutated: () => void
  isLoading?: boolean
}

// Quince is the background system voice runtime & MCP server (handled in ServicesView)
// Applications Grid: Plum - Kiwi - Banana - Lemon - Cherry
const EXCLUDED_FRUITS = new Set(['quince'])
const SORT_ORDER = ['plum', 'kiwi', 'banana', 'lemon', 'cherry']

/**
 * OverviewView — Fruit Family Design System Specification
 *
 * Operations Cockpit: Hardware telemetry, reverse proxy orchestration, and local applications.
 * Typography strictly adheres to the 7-size scale (Section 2.2).
 */
export const OverviewView: React.FC<OverviewViewProps> = ({
  overview,
  telemetry,
  nginxData,
  onMutated,
  isLoading,
}) => {
  const displayedFruits = (overview?.fruits || [])
    .filter(f => !EXCLUDED_FRUITS.has(f.id.toLowerCase()))
    .sort((a, b) => {
      const idxA = SORT_ORDER.indexOf(a.id.toLowerCase())
      const idxB = SORT_ORDER.indexOf(b.id.toLowerCase())
      return (idxA === -1 ? 99 : idxA) - (idxB === -1 ? 99 : idxB)
    })

  return (
    <div className="space-y-6 animate-page-enter">
      {/* Page Header (PageTitle 24px / 1.5rem, Section 2.2) */}
      <div className="flex flex-col sm:flex-row sm:items-baseline justify-between gap-2">
        <h1 className="text-pagetitle font-extrabold tracking-tight text-stone-900 dark:text-stone-50 font-sans">
          Operations & Ecosystem
        </h1>
      </div>

      {/* Real-time Hardware Telemetry (CPU, RAM, GPU, VRAM) */}
      <TelemetryHUD telemetry={telemetry} isLoading={isLoading && !telemetry} />

      {/* Unified Edge Proxy & Ecosystem Master Command Bar */}
      <SystemCommandBar
        nginxData={nginxData}
        metrics={overview?.metrics || null}
        onMutated={onMutated}
      />

      {/* Applications Grid: Models Card first, followed by Plum, Kiwi, Banana, Lemon, Cherry */}
      <section className="pt-2">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-micro font-bold uppercase tracking-wider text-stone-400 dark:text-stone-500 font-sans">
            Applications
          </h2>
          <span className="font-mono text-caption text-stone-400 dark:text-stone-500">
            {displayedFruits.filter(f => f.is_running || f.is_android_client).length} / {displayedFruits.length} Active
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4 sm:gap-5">
          {/* Routine AI Models Master Card placed first */}
          <ModelsCard
            services={overview?.services || []}
            onMutated={onMutated}
          />

          {displayedFruits.map(fruit => (
            <FruitCard key={fruit.id} fruit={fruit} onMutated={onMutated} />
          ))}
        </div>
      </section>
    </div>
  )
}
