import React, { useState } from 'react'
import { TerminalSquare, Radio } from 'lucide-react'
import { LogViewer } from '../components/LogViewer'
import { RouteMatrix } from '../components/RouteMatrix'
import { OperationHistory } from '../components/OperationHistory'
import type { ServiceStatus, RouteStatus, OperationRecord } from '../types/api'

interface DiagnosticsViewProps {
  services: ServiceStatus[]
  routes: RouteStatus[]
  operations: OperationRecord[]
  selectedLogService: string
  setSelectedLogService: (id: string) => void
}

export const DiagnosticsView: React.FC<DiagnosticsViewProps> = ({
  services,
  routes,
  operations,
  selectedLogService,
  setSelectedLogService,
}) => {
  const [subTab, setSubTab] = useState<'logs' | 'routes'>('logs')

  return (
    <div className="space-y-6">
      {/* Header & Sub-tab navigation */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-stone-900 dark:text-stone-50 font-sans">
            Diagnostics
          </h1>
          <p className="mt-1 text-sm text-stone-500 dark:text-stone-400 font-sans">
            Real-time stdout/stderr console, route reachability, and operations audit.
          </p>
        </div>

        {/* Sub-tab pills */}
        <div className="flex items-center gap-1.5 self-start sm:self-auto shrink-0" role="tablist">
          <button
            type="button"
            onClick={() => setSubTab('logs')}
            className={`focus-ring flex items-center gap-1.5 rounded-full px-3.5 py-1.5 text-xs font-semibold font-sans whitespace-nowrap shrink-0 transition-all ${
              subTab === 'logs'
                ? 'bg-stone-900 text-white dark:bg-stone-100 dark:text-stone-900 shadow-xs'
                : 'text-stone-600 dark:text-stone-300 hover:bg-stone-100 dark:hover:bg-stone-800'
            }`}
          >
            <TerminalSquare className="h-3.5 w-3.5 shrink-0" />
            <span className="whitespace-nowrap">Live Logs</span>
          </button>

          <button
            type="button"
            onClick={() => setSubTab('routes')}
            className={`focus-ring flex items-center gap-1.5 rounded-full px-3.5 py-1.5 text-xs font-semibold font-sans whitespace-nowrap shrink-0 transition-all ${
              subTab === 'routes'
                ? 'bg-stone-900 text-white dark:bg-stone-100 dark:text-stone-900 shadow-xs'
                : 'text-stone-600 dark:text-stone-300 hover:bg-stone-100 dark:hover:bg-stone-800'
            }`}
          >
            <Radio className="h-3.5 w-3.5 shrink-0" />
            <span className="whitespace-nowrap">Routes & Audit ({routes.length})</span>
          </button>
        </div>
      </div>

      {/* Active Sub-tab View */}
      {subTab === 'logs' ? (
        <LogViewer
          services={services}
          selectedServiceId={selectedLogService}
          onSelectService={setSelectedLogService}
        />
      ) : (
        <div className="space-y-6">
          <RouteMatrix routes={routes} />
          <OperationHistory operations={operations} />
        </div>
      )}
    </div>
  )
}
