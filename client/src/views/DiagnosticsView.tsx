import React, { useState } from 'react'
import { TerminalSquare, Radio } from 'lucide-react'
import { LogViewer } from '../components/LogViewer'
import { RouteMatrix } from '../components/RouteMatrix'
import { OperationHistory } from '../components/OperationHistory'
import { SegmentedControl, type SegmentOption } from '../components/SegmentedControl'
import { playScroll } from '../lib/sound'
import { useShiftArrowCycle } from '../lib/keyboard'
import type { ServiceStatus, RouteStatus, OperationRecord } from '../types/api'

interface DiagnosticsViewProps {
  services: ServiceStatus[]
  routes: RouteStatus[]
  operations: OperationRecord[]
  selectedLogService: string
  setSelectedLogService: (id: string) => void
}

type SubTab = 'logs' | 'routes'
const SUB_TABS: SubTab[] = ['logs', 'routes']

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

  // Shift + ArrowLeft / ArrowRight cycles Diagnostics sub-tabs (Live Logs <-> Routes & Audit)
  useShiftArrowCycle({
    items: SUB_TABS,
    current: subTab,
    onSelect: setSubTab,
    onCycle: playScroll,
  })

  const subTabOptions: SegmentOption<SubTab>[] = [
    { id: 'logs', label: 'Live Logs', icon: TerminalSquare },
    { id: 'routes', label: 'Routes & Audit', count: routes.length, icon: Radio },
  ]

  return (
    <div
      className={
        subTab === 'logs'
          ? 'h-[calc(100dvh-10rem)] sm:h-[calc(100dvh-6.25rem)] flex flex-col gap-4 animate-page-enter'
          : 'space-y-6 animate-page-enter'
      }
    >
      {/* Header & Sub-tab navigation */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 shrink-0">
        <h1 className="text-pagetitle font-extrabold tracking-tight text-stone-900 dark:text-stone-50 font-sans">
          Diagnostics
        </h1>

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
        <div className="flex-1 min-h-0 flex flex-col">
          <LogViewer
            services={services}
            selectedServiceId={selectedLogService}
            onSelectService={setSelectedLogService}
          />
        </div>
      ) : (
        <div className="space-y-6">
          <RouteMatrix routes={routes} />
          <OperationHistory operations={operations} />
        </div>
      )}
    </div>
  )
}
