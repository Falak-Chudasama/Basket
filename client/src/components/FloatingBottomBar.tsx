import React, { useRef, useEffect, useState } from 'react'
import { LayoutDashboard, Cpu, TerminalSquare } from 'lucide-react'
import { playEnter, playScroll } from '../lib/sound'

export type ActiveTab = 'overview' | 'services' | 'diagnostics'

interface FloatingBottomBarProps {
  activeTab: ActiveTab
  setActiveTab: (tab: ActiveTab) => void
}

/**
 * FloatingBottomBar — Fruit Family Design System Specification (Section 4.1, 5.6 & 6.2)
 *
 * Dedicated mobile navigation pattern (< 640px).
 * Docked bottom capsule with 48dp touch targets, glass-capsule tier (blur 15px, 0.20 fill),
 * and 300ms sliding active pill indicator.
 */
export const FloatingBottomBar: React.FC<FloatingBottomBarProps> = ({
  activeTab,
  setActiveTab,
}) => {
  const containerRef = useRef<HTMLDivElement>(null)
  const [indicatorStyle, setIndicatorStyle] = useState<{ left: number; width: number }>({
    left: 0,
    width: 0,
  })
  const buttonRefs = useRef<Map<ActiveTab, HTMLButtonElement>>(new Map())

  const navItems = [
    { id: 'overview' as ActiveTab, label: 'Overview', icon: LayoutDashboard },
    { id: 'services' as ActiveTab, label: 'Services', icon: Cpu },
    { id: 'diagnostics' as ActiveTab, label: 'Logs', icon: TerminalSquare },
  ]

  useEffect(() => {
    const btn = buttonRefs.current.get(activeTab)
    const container = containerRef.current
    if (btn && container) {
      const btnRect = btn.getBoundingClientRect()
      const containerRect = container.getBoundingClientRect()
      setIndicatorStyle({
        left: btnRect.left - containerRect.left,
        width: btnRect.width,
      })
    }
  }, [activeTab])

  const handleSelect = (id: ActiveTab) => {
    if (id !== activeTab) {
      playScroll()
      setActiveTab(id)
    }
  }

  return (
    <nav
      aria-label="Mobile Navigation Dock"
      className="fixed bottom-3 left-4 right-4 z-40 max-w-sm mx-auto sm:hidden"
    >
      <div
        ref={containerRef}
        className="glass-capsule relative flex items-center justify-between rounded-full p-1.5 shadow-floating"
      >
        {/* Sliding Indicator Pill (300ms cubic-bezier(0.2, 0.8, 0.2, 1)) */}
        {indicatorStyle.width > 0 && (
          <div
            className="absolute top-1.5 bottom-1.5 rounded-full bg-stone-900 text-white dark:bg-stone-100 shadow-xs pointer-events-none transition-all duration-300 ease-[cubic-bezier(0.2,0.8,0.2,1)]"
            style={{
              left: `${indicatorStyle.left}px`,
              width: `${indicatorStyle.width}px`,
            }}
          />
        )}

        {navItems.map(({ id, label, icon: Icon }) => {
          const isActive = activeTab === id
          return (
            <button
              key={id}
              ref={el => {
                if (el) buttonRefs.current.set(id, el)
                else buttonRefs.current.delete(id)
              }}
              type="button"
              role="tab"
              aria-selected={isActive}
              onClick={() => handleSelect(id)}
              className={`focus-ring relative z-10 flex flex-1 items-center justify-center gap-1.5 min-h-[48px] px-3 rounded-full text-xs font-semibold font-sans transition-colors duration-200 ${
                isActive
                  ? 'text-white dark:text-stone-900'
                  : 'text-stone-600 dark:text-stone-300 hover:text-stone-900 dark:hover:text-white'
              }`}
            >
              <Icon className="h-4 w-4 shrink-0" />
              <span>{label}</span>
            </button>
          )
        })}
      </div>
    </nav>
  )
}
