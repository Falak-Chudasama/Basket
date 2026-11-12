import React, { useState } from 'react'
import { Server, Search, Sparkles, Database, Box } from 'lucide-react'
import { ServiceRow } from '../components/ServiceRow'
import type { ServiceStatus } from '../types/api'

interface ServicesViewProps {
  services: ServiceStatus[]
  onMutated: () => void
  onViewLogs: (serviceId: string) => void
}

type FilterCategory = 'all' | 'ai' | 'core' | 'fruits'

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

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-baseline justify-between gap-2">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-stone-900 dark:text-stone-50 font-sans">
            Services & Models
          </h1>
          <p className="mt-1 text-sm text-stone-500 dark:text-stone-400 font-sans">
            Low-level daemon control, llama.cpp models, STT/TTS engines, and databases.
          </p>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        {/* Filter Pills */}
        <div className="flex flex-wrap items-center gap-1.5 shrink-0" role="tablist">
          <button
            type="button"
            onClick={() => setFilter('all')}
            className={`focus-ring flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-semibold font-sans whitespace-nowrap shrink-0 transition-all ${
              filter === 'all'
                ? 'bg-stone-900 text-white dark:bg-stone-100 dark:text-stone-900 shadow-xs'
                : 'text-stone-600 dark:text-stone-300 hover:bg-stone-100 dark:hover:bg-stone-800'
            }`}
          >
            <Server className="h-3 w-3 shrink-0" />
            <span className="whitespace-nowrap">All ({services.length})</span>
          </button>

          <button
            type="button"
            onClick={() => setFilter('ai')}
            className={`focus-ring flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-semibold font-sans whitespace-nowrap shrink-0 transition-all ${
              filter === 'ai'
                ? 'bg-stone-900 text-white dark:bg-stone-100 dark:text-stone-900 shadow-xs'
                : 'text-stone-600 dark:text-stone-300 hover:bg-stone-100 dark:hover:bg-stone-800'
            }`}
          >
            <Sparkles className="h-3 w-3 shrink-0" />
            <span className="whitespace-nowrap">AI & Audio ({aiCount})</span>
          </button>

          <button
            type="button"
            onClick={() => setFilter('core')}
            className={`focus-ring flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-semibold font-sans whitespace-nowrap shrink-0 transition-all ${
              filter === 'core'
                ? 'bg-stone-900 text-white dark:bg-stone-100 dark:text-stone-900 shadow-xs'
                : 'text-stone-600 dark:text-stone-300 hover:bg-stone-100 dark:hover:bg-stone-800'
            }`}
          >
            <Database className="h-3 w-3 shrink-0" />
            <span className="whitespace-nowrap">Core & DB ({coreCount})</span>
          </button>

          <button
            type="button"
            onClick={() => setFilter('fruits')}
            className={`focus-ring flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-semibold font-sans whitespace-nowrap shrink-0 transition-all ${
              filter === 'fruits'
                ? 'bg-stone-900 text-white dark:bg-stone-100 dark:text-stone-900 shadow-xs'
                : 'text-stone-600 dark:text-stone-300 hover:bg-stone-100 dark:hover:bg-stone-800'
            }`}
          >
            <Box className="h-3 w-3 shrink-0" />
            <span className="whitespace-nowrap">Apps ({fruitCount})</span>
          </button>
        </div>

        {/* Search */}
        <div className="relative">
          <Search className="w-3.5 h-3.5 text-stone-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search services..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="pl-8 pr-3 py-1.5 rounded-full bg-white dark:bg-[#181915] border border-black/[0.06] dark:border-white/[0.08] text-xs font-sans text-stone-800 dark:text-stone-200 outline-none focus:ring-2 focus:ring-basket-500 w-full sm:w-56 shadow-2xs"
          />
        </div>
      </div>

      {/* Services List */}
      <div className="space-y-2">
        {filteredServices.length === 0 ? (
          <div className="p-8 text-center text-xs font-sans text-stone-400 dark:text-stone-500 rounded-2xl border border-black/[0.05] dark:border-white/[0.06] bg-white dark:bg-[#181915]">
            No services match the selected criteria.
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
