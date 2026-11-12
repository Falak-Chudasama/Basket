import React from 'react'
import { CheckCircle2, XCircle } from 'lucide-react'
import type { OperationRecord } from '../types/api'

interface OperationHistoryProps {
  operations: OperationRecord[]
}

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
    <div className="rounded-2xl border border-black/[0.06] dark:border-white/[0.08] bg-white dark:bg-[#181915] p-5 shadow-soft">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="font-sans font-bold text-base text-stone-900 dark:text-stone-100">
            Operations Audit Log
          </h3>
          <p className="text-xs font-sans text-stone-500 dark:text-stone-400">
            Recorded server actions, process dispatches, and execution latencies.
          </p>
        </div>
        <span className="font-mono text-xs text-stone-400 dark:text-stone-500">
          {operations.length} Recorded
        </span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs font-mono">
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
                <tr key={op.id} className="hover:bg-stone-50/60 dark:hover:bg-stone-900/40 transition-colors whitespace-nowrap">
                  <td className="py-2 text-stone-500 dark:text-stone-400 whitespace-nowrap">
                    {formatTimestamp(op.timestamp)}
                  </td>
                  <td className="py-2 font-sans font-semibold text-stone-900 dark:text-stone-100 whitespace-nowrap">
                    {op.service_id}
                  </td>
                  <td className="py-2 whitespace-nowrap">
                    <span className="uppercase text-[10px] font-bold tracking-wider px-1.5 py-0.5 rounded bg-stone-100 dark:bg-stone-800 text-stone-700 dark:text-stone-300 whitespace-nowrap">
                      {op.action}
                    </span>
                  </td>
                  <td className="py-2 text-stone-500 dark:text-stone-400 whitespace-nowrap">
                    {op.duration_ms}ms
                  </td>
                  <td className="py-2 text-right whitespace-nowrap">
                    <span
                      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold whitespace-nowrap ${
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
