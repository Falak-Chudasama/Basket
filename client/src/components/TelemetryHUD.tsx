import React from 'react'
import { Cpu, HardDrive, Zap, Layers, Thermometer } from 'lucide-react'
import type { SystemTelemetry } from '../types/api'

interface TelemetryHUDProps {
  telemetry: SystemTelemetry | null
  isLoading?: boolean
}

// Smooth continuous color gradient: Emerald -> Lime -> Amber -> Rose without abrupt jumps
const getDynamicBarColor = (pct: number): string => {
  const clamped = Math.max(0, Math.min(100, pct))
  let hue: number
  if (clamped <= 50) {
    // 0% -> 150 (emerald), 50% -> 90 (lime)
    hue = 150 - (clamped / 50) * 60
  } else if (clamped <= 80) {
    // 50% -> 90 (lime), 80% -> 40 (amber)
    hue = 90 - ((clamped - 50) / 30) * 50
  } else {
    // 80% -> 40 (amber), 100% -> 0 (rose/red)
    hue = 40 - ((clamped - 80) / 20) * 40
  }
  return `hsl(${Math.round(hue)}, 80%, 48%)`
}

export const TelemetryHUD: React.FC<TelemetryHUDProps> = ({ telemetry, isLoading }) => {
  if (!telemetry && isLoading) {
    return (
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 animate-pulse">
        {[1, 2, 3, 4].map(i => (
          <div
            key={i}
            className="h-24 rounded-2xl bg-white dark:bg-[#181915] border border-black/[0.05] dark:border-white/[0.06] p-4"
          />
        ))}
      </div>
    )
  }

  if (!telemetry) return null

  const { cpu, memory, gpu } = telemetry

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
      {/* CPU */}
      <div className="rounded-2xl border border-black/[0.06] dark:border-white/[0.08] bg-white dark:bg-[#181915] p-4 shadow-soft transition-colors">
        <div className="flex items-center justify-between gap-1 text-xs font-sans text-stone-500 dark:text-stone-400 mb-2">
          <div className="flex items-center gap-1.5 font-medium shrink-0">
            <Cpu className="h-3.5 w-3.5 shrink-0" />
            <span className="whitespace-nowrap">CPU</span>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            {cpu.temperature_c !== undefined && cpu.temperature_c !== null && (
              <span className="flex items-center gap-0.5 font-mono text-[11px] text-stone-500 dark:text-stone-400 whitespace-nowrap shrink-0" title="CPU Temperature">
                <Thermometer className="h-3 w-3 text-amber-500 shrink-0" />
                <span>{cpu.temperature_c}°C</span>
              </span>
            )}
            <span className="font-mono text-[11px] text-stone-400 dark:text-stone-500 whitespace-nowrap shrink-0">
              {cpu.logical_cores} Cores
            </span>
          </div>
        </div>
        <div className="flex items-baseline justify-between mb-2.5">
          <span className="font-mono text-2xl font-bold tracking-tight text-stone-900 dark:text-stone-50 whitespace-nowrap">
            {cpu.utilization_pct.toFixed(1)}%
          </span>
        </div>
        <div className="h-1.5 w-full rounded-full bg-stone-100 dark:bg-stone-800 overflow-hidden">
          <div
            className="h-full rounded-full transition-all duration-700 ease-out"
            style={{
              width: `${Math.min(100, Math.max(3, cpu.utilization_pct))}%`,
              backgroundColor: getDynamicBarColor(cpu.utilization_pct),
            }}
          />
        </div>
      </div>

      {/* RAM */}
      <div className="rounded-2xl border border-black/[0.06] dark:border-white/[0.08] bg-white dark:bg-[#181915] p-4 shadow-soft transition-colors">
        <div className="flex items-center justify-between gap-1 text-xs font-sans text-stone-500 dark:text-stone-400 mb-2">
          <div className="flex items-center gap-1.5 font-medium shrink-0">
            <HardDrive className="h-3.5 w-3.5 shrink-0" />
            <span className="whitespace-nowrap">RAM</span>
          </div>
          <span className="font-mono text-[11px] text-stone-400 dark:text-stone-500 whitespace-nowrap shrink-0">
            {memory.used_gb} / {memory.total_gb} GB
          </span>
        </div>
        <div className="flex items-baseline justify-between mb-2.5">
          <span className="font-mono text-2xl font-bold tracking-tight text-stone-900 dark:text-stone-50 whitespace-nowrap">
            {memory.utilization_pct.toFixed(1)}%
          </span>
        </div>
        <div className="h-1.5 w-full rounded-full bg-stone-100 dark:bg-stone-800 overflow-hidden">
          <div
            className="h-full rounded-full transition-all duration-700 ease-out"
            style={{
              width: `${Math.min(100, Math.max(3, memory.utilization_pct))}%`,
              backgroundColor: getDynamicBarColor(memory.utilization_pct),
            }}
          />
        </div>
      </div>

      {/* GPU */}
      <div className="rounded-2xl border border-black/[0.06] dark:border-white/[0.08] bg-white dark:bg-[#181915] p-4 shadow-soft transition-colors">
        <div className="flex items-center justify-between gap-1 text-xs font-sans text-stone-500 dark:text-stone-400 mb-2">
          <div className="flex items-center gap-1.5 font-medium shrink-0">
            <Zap className="h-3.5 w-3.5 shrink-0" />
            <span className="whitespace-nowrap">GPU</span>
          </div>
          {gpu.available && (
            <span className="flex items-center gap-0.5 font-mono text-[11px] text-stone-500 dark:text-stone-400 whitespace-nowrap shrink-0" title="GPU Temperature">
              <Thermometer className="h-3 w-3 text-rose-500 shrink-0" />
              <span>{gpu.temperature_c}°C</span>
            </span>
          )}
        </div>
        <div className="flex items-baseline justify-between mb-2.5">
          <span className="font-mono text-2xl font-bold tracking-tight text-stone-900 dark:text-stone-50 whitespace-nowrap">
            {gpu.available ? `${gpu.gpu_utilization_pct}%` : 'N/A'}
          </span>
        </div>
        <div className="h-1.5 w-full rounded-full bg-stone-100 dark:bg-stone-800 overflow-hidden">
          <div
            className="h-full rounded-full transition-all duration-700 ease-out"
            style={{
              width: `${Math.min(100, Math.max(3, gpu.gpu_utilization_pct))}%`,
              backgroundColor: getDynamicBarColor(gpu.gpu_utilization_pct),
            }}
          />
        </div>
      </div>

      {/* VRAM */}
      <div className="rounded-2xl border border-black/[0.06] dark:border-white/[0.08] bg-white dark:bg-[#181915] p-4 shadow-soft transition-colors">
        <div className="flex items-center justify-between gap-1 text-xs font-sans text-stone-500 dark:text-stone-400 mb-2">
          <div className="flex items-center gap-1.5 font-medium shrink-0">
            <Layers className="h-3.5 w-3.5 shrink-0" />
            <span className="whitespace-nowrap">VRAM</span>
          </div>
          {gpu.available && (
            <span className="font-mono text-[11px] text-stone-400 dark:text-stone-500 whitespace-nowrap shrink-0">
              {(gpu.vram_used_mb / 1024).toFixed(1)} / {(gpu.vram_total_mb / 1024).toFixed(1)} GB
            </span>
          )}
        </div>
        <div className="flex items-baseline justify-between mb-2.5">
          <span className="font-mono text-2xl font-bold tracking-tight text-stone-900 dark:text-stone-50 whitespace-nowrap">
            {gpu.available ? `${gpu.vram_pct.toFixed(1)}%` : 'N/A'}
          </span>
        </div>
        <div className="h-1.5 w-full rounded-full bg-stone-100 dark:bg-stone-800 overflow-hidden">
          <div
            className="h-full rounded-full transition-all duration-700 ease-out"
            style={{
              width: `${Math.min(100, Math.max(3, gpu.vram_pct))}%`,
              backgroundColor: getDynamicBarColor(gpu.vram_pct),
            }}
          />
        </div>
      </div>
    </div>
  )
}
