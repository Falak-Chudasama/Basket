import React, { useState } from 'react'
import { Server, Search, Sparkles, Database, Box } from 'lucide-react'
import { ServiceRow } from '../components/ServiceRow'
import { SegmentedControl, type SegmentOption } from '../components/SegmentedControl'
import type { ServiceStatus } from '../types/api'

interface ServicesViewProps {
  services: ServiceStatus[]
  onMutated: () => void
  onViewLogs: (serviceId: string) => void
}

type FilterCategory = 'all' | 'ai' | 'core' | 'fruits'

/**
 * ServicesView — Fruit Family Design System Specification
 *
 * Daemon and model management with SegmentedControl (Section 5.7),
 * Text Input (Section 5.3), and ServiceRow (Section 5.5).
 */
export const ServicesView: React.FC<ServicesViewProps> = ({
  services,
  onMutated,
  onViewLogs,
}) => {
  const [filter, setFilter] = useState<FilterCategory>('all')
  const [search, setSearch] = useState('')

  const isAIMatch = (s: ServiceStatus) => ['llm', 'speech'].includes(s.category)
  const isCoreMatch = (s: ServiceStatus) => ['infrastructure', 'database', 'proxy', 'control'].includes(s.category)
  const isFruitMatch = (s: ServiceStatus) => s.category === 'fruit'

  const filteredServices = services.filter(s => {
    if (filter === 'ai' && !isAIMatch(s)) return false
    if (filter === 'core' && !isCoreMatch(s)) return false
    if (filter === 'fruits' && !isFruitMatch(s)) return false

    if (search) {
      const q = search.toLowerCase()
      const match =
        s.name.toLowerCase().includes(q) ||
        s.id.toLowerCase().includes(q) ||
        (s.port && s.port.toString().includes(q)) ||
        s.description.toLowerCase().includes(q)
      if (!match) return false
    }

    return true
  })

  const aiCount = services.filter(isAIMatch).length
  const coreCount = services.filter(isCoreMatch).length
  const fruitCount = services.filter(isFruitMatch).length

  const filterOptions: SegmentOption<FilterCategory>[] = [
    { id: 'all', label: 'All', count: services.length, icon: Server },
    { id: 'ai', label: 'AI & Audio', count: aiCount, icon: Sparkles },
    { id: 'core', label: 'Core', count: coreCount, icon: Database },
    { id: 'fruits', label: 'Fruits', count: fruitCount, icon: Box },
  ]

  return (
    <div className="space-y-6 animate-page-enter">
      {/* Header (PageTitle 24px / 1.5rem, Section 2.2) */}
      <div className="flex flex-col sm:flex-row sm:items-baseline justify-between gap-2">
        <div>
          <h1 className="text-pagetitle font-extrabold tracking-tight text-stone-900 dark:text-stone-50 font-sans">
            Services & Models
          </h1>
          <p className="mt-1 text-body text-stone-500 dark:text-stone-400 font-sans">
            Low-level daemon control, llama.cpp models, STT/TTS engines, and databases.
          </p>
        </div>
      </div>

      {/* Filter Segmented Control & Search Input (Section 5.7 & 5.3) */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        {/* Segmented Control with 300ms sliding indicator */}
        <SegmentedControl<FilterCategory>
          options={filterOptions}
          value={filter}
          onChange={setFilter}
          ariaLabel="Service category filters"
        />

        {/* Search Field (Section 5.3: height 44px, radius 12px, two-layer focus ring) */}
        <div className="relative w-full sm:w-64">
          <Search className="w-4 h-4 text-stone-400 absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
          <input
            type="text"
            placeholder="Search services or ports..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="focus-ring w-full h-[44px] pl-10 pr-4 rounded-xl glass-card text-body font-sans text-stone-900 dark:text-stone-100 placeholder:text-stone-400 dark:placeholder:text-stone-500 transition-all outline-none"
          />
        </div>
      </div>

      {/* Services List Rows (Section 5.5) */}
      <div className="space-y-2.5">
        {filteredServices.length === 0 ? (
          <div className="glass-card rounded-2xl p-12 text-center">
            <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-stone-100 dark:bg-stone-800 text-stone-400 mb-3">
              <Server className="h-6 w-6" />
            </div>
            <h3 className="font-sans font-bold text-subtitle text-stone-900 dark:text-stone-100">
              No matching services
            </h3>
            <p className="text-caption font-sans text-stone-500 dark:text-stone-400 mt-1 max-w-sm mx-auto">
              No services match your active search or filter selection.
            </p>
          </div>
        ) : (
          filteredServices.map(service => (
            <ServiceRow
              key={service.id}
              service={service}
              onMutated={onMutated}
              onViewLogs={onViewLogs}
            />
          ))
        )}
      </div>
    </div>
  )
}
