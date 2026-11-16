import React, { useState } from 'react'
import { TerminalSquare, Radio } from 'lucide-react'
import { LogViewer } from '../components/LogViewer'
import { RouteMatrix } from '../components/RouteMatrix'
import { OperationHistory } from '../components/OperationHistory'
import { SegmentedControl, type SegmentOption } from '../components/SegmentedControl'
import type { ServiceStatus, RouteStatus, OperationRecord } from '../types/api'

interface DiagnosticsViewProps {
  services: ServiceStatus[]
  routes: RouteStatus[]
  operations: OperationRecord[]
  selectedLogService: string
  setSelectedLogService: (id: string) => void
}

type SubTab = 'logs' | 'routes'

/**
 * DiagnosticsView — Fruit Family Design System Specification
 *
 * Real-time stdout/stderr console, route reachability matrix, and operations audit log.
 * Controlled via SegmentedControl (Section 5.7).
 */
export const DiagnosticsView: React.FC<DiagnosticsViewProps> = ({
  services,
  routes,
  operations,
  selectedLogService,
  setSelectedLogService,
}) => {
  const [subTab, setSubTab] = useState<SubTab>('logs')

  const subTabOptions: SegmentOption<SubTab>[] = [
    { id: 'logs', label: 'Live Logs', icon: TerminalSquare },
    { id: 'routes', label: 'Routes & Audit', count: routes.length, icon: Radio },
  ]

  return (
    <div className="space-y-6 animate-page-enter">
      {/* Header & Sub-tab navigation */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-pagetitle font-extrabold tracking-tight text-stone-900 dark:text-stone-50 font-sans">
            Diagnostics
          </h1>
          <p className="mt-1 text-body text-stone-500 dark:text-stone-400 font-sans">
            Real-time stdout/stderr console, route reachability, and operations audit.
          </p>
        </div>

        {/* Sub-tab Segmented Control (Section 5.7) */}
        <SegmentedControl<SubTab>
          options={subTabOptions}
          value={subTab}
          onChange={setSubTab}
          ariaLabel="Diagnostics sub-views"
        />
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
