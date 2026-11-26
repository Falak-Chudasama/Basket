import React from 'react'
import { ExternalLink, CheckCircle2, XCircle } from 'lucide-react'
import type { RouteStatus } from '../types/api'

interface RouteMatrixProps {
  routes: RouteStatus[]
}

/**
 * RouteMatrix — Fruit Family Design System Specification (Section 5.4 & 5.10)
 *
 * Reverse Proxy routing table adhering to .glass-card tier and disciplined 7-size typography.
 */
export const RouteMatrix: React.FC<RouteMatrixProps> = ({ routes }) => {
  return (
    <div className="glass-card rounded-2xl p-5 shadow-soft transition-all duration-200 hover:border-stone-300 dark:hover:border-stone-700 hover:shadow-lift">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-sans font-bold text-subtitle text-stone-900 dark:text-stone-100">
          Reverse Proxy Routes
        </h3>
        <span className="font-mono text-caption text-stone-400 dark:text-stone-500">
          {routes.filter(r => r.is_live).length} / {routes.length} Active
        </span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-caption font-mono">
          <thead>
            <tr className="border-b border-black/[0.06] dark:border-white/[0.08] text-stone-400 dark:text-stone-500 font-sans whitespace-nowrap">
              <th className="pb-2.5 font-semibold whitespace-nowrap">Service</th>
              <th className="pb-2.5 font-semibold whitespace-nowrap">Public Domain</th>
              <th className="pb-2.5 font-semibold whitespace-nowrap">Upstream Target</th>
              <th className="pb-2.5 font-semibold whitespace-nowrap">Type</th>
              <th className="pb-2.5 font-semibold text-right whitespace-nowrap">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-black/[0.04] dark:divide-white/[0.04]">
            {routes.map(r => (
              <tr key={r.id} className="hover:bg-black/[0.02] dark:hover:bg-white/[0.02] transition-colors whitespace-nowrap">
                <td className="py-2.5 font-sans font-semibold text-stone-900 dark:text-stone-100 whitespace-nowrap">
                  {r.service}
                </td>
                <td className="py-2.5 whitespace-nowrap">
                  <a
                    href={r.reverse_proxy_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="focus-ring inline-flex items-center gap-1 text-stone-600 dark:text-stone-300 hover:text-stone-900 dark:hover:text-white transition whitespace-nowrap rounded"
                  >
                    <span>{r.reverse_proxy_url}</span>
                    <ExternalLink className="w-3 h-3 text-stone-400 shrink-0" />
                  </a>
                </td>
                <td className="py-2.5 text-stone-500 dark:text-stone-400 truncate max-w-xs whitespace-nowrap">
                  {r.actual_destination}
                </td>
                <td className="py-2.5 whitespace-nowrap">
                  <span className="text-micro uppercase font-bold tracking-wider px-1.5 py-0.5 rounded bg-stone-100 dark:bg-stone-800 text-stone-600 dark:text-stone-400 whitespace-nowrap">
                    {r.type}
                  </span>
                </td>
                <td className="py-2.5 text-right whitespace-nowrap">
                  <span
                    className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-micro font-semibold whitespace-nowrap ${
                      r.is_live
                        ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400'
                        : 'bg-rose-500/10 text-rose-600 dark:text-rose-400'
                    }`}
                  >
                    {r.is_live ? <CheckCircle2 className="w-3 h-3 shrink-0" /> : <XCircle className="w-3 h-3 shrink-0" />}
                    <span>{r.status_code || r.message}</span>
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
