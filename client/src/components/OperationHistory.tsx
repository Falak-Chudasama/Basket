import React from 'react'
import { CheckCircle2, XCircle } from 'lucide-react'
import type { OperationRecord } from '../types/api'

interface OperationHistoryProps {
  operations: OperationRecord[]
}

/**
 * OperationHistory — Fruit Family Design System Specification (Section 5.4 & 5.10)
 *
 * Audit log table with .glass-card tier, disciplined 7-size typography, and status badges.
 */
export const OperationHistory: React.FC<OperationHistoryProps> = ({ operations }) => {
  const formatTimestamp = (iso: string) => {
    try {
      const d = new Date(iso)
      return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
    } catch {
      return iso
    }
  }

  return (
    <div className="glass-card rounded-2xl p-5 shadow-soft transition-all duration-200 hover:border-stone-300 dark:hover:border-stone-700 hover:shadow-lift">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="font-sans font-bold text-subtitle text-stone-900 dark:text-stone-100">
            Operations Audit Log
          </h3>
          <p className="text-caption font-sans text-stone-500 dark:text-stone-400">
            Recorded server actions, process dispatches, and execution latencies.
          </p>
        </div>
        <span className="font-mono text-caption text-stone-400 dark:text-stone-500">
          {operations.length} Recorded
        </span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-caption font-mono">
          <thead>
            <tr className="border-b border-black/[0.06] dark:border-white/[0.08] text-stone-400 dark:text-stone-500 font-sans whitespace-nowrap">
              <th className="pb-2.5 font-semibold whitespace-nowrap">Time</th>
              <th className="pb-2.5 font-semibold whitespace-nowrap">Target Service</th>
              <th className="pb-2.5 font-semibold whitespace-nowrap">Action</th>
              <th className="pb-2.5 font-semibold whitespace-nowrap">Duration</th>
              <th className="pb-2.5 font-semibold text-right whitespace-nowrap">Result</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-black/[0.04] dark:divide-white/[0.04]">
            {operations.length === 0 ? (
              <tr>
                <td colSpan={5} className="py-6 text-center text-stone-400 dark:text-stone-600 font-sans whitespace-nowrap">
                  No operations executed yet in this session.
                </td>
              </tr>
            ) : (
              operations.map(op => (
                <tr key={op.id} className="hover:bg-black/[0.02] dark:hover:bg-white/[0.02] transition-colors whitespace-nowrap">
                  <td className="py-2.5 text-stone-500 dark:text-stone-400 whitespace-nowrap">
                    {formatTimestamp(op.timestamp)}
                  </td>
                  <td className="py-2.5 font-sans font-semibold text-stone-900 dark:text-stone-100 whitespace-nowrap">
                    {op.service_id}
                  </td>
                  <td className="py-2.5 whitespace-nowrap">
                    <span className="uppercase text-micro font-bold tracking-wider px-1.5 py-0.5 rounded bg-stone-100 dark:bg-stone-800 text-stone-700 dark:text-stone-300 whitespace-nowrap">
                      {op.action}
                    </span>
                  </td>
                  <td className="py-2.5 text-stone-500 dark:text-stone-400 whitespace-nowrap">
                    {op.duration_ms}ms
                  </td>
                  <td className="py-2.5 text-right whitespace-nowrap">
                    <span
                      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-micro font-semibold whitespace-nowrap ${
                        op.status === 'success'
                          ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400'
                          : 'bg-rose-500/10 text-rose-600 dark:text-rose-400'
                      }`}
                    >
                      {op.status === 'success' ? (
                        <CheckCircle2 className="w-3 h-3 shrink-0" />
                      ) : (
                        <XCircle className="w-3 h-3 shrink-0" />
                      )}
                      <span className="uppercase whitespace-nowrap">{op.status}</span>
                    </span>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
