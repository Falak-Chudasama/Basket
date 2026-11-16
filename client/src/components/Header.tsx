import React, { useRef, useEffect, useState } from 'react'
import {
  Sun,
  Moon,
  RefreshCw,
  LayoutDashboard,
  Cpu,
  TerminalSquare,
} from 'lucide-react'
import { useTheme } from '../context/ThemeContext'
import { useSound } from '../context/SoundContext'

export type ActiveTab = 'overview' | 'services' | 'diagnostics'

interface HeaderProps {
  activeTab: ActiveTab
  setActiveTab: (tab: ActiveTab) => void
  isRefreshing: boolean
  onRefresh: () => void
  isOnline: boolean
}

/**
 * Header — Fruit Family Design System Specification (Section 4.1 & 5.6)
 *
 * Pinned stationary floating capsule navbar docked at top-3.
 * Stays stationary at the top of the viewport during scrolling.
 * Features brand wordmark, router tabs with 300ms sliding active pill indicator,
 * user-facing audio sound toggle, theme mode toggle, and manual telemetry refresh.
 */
export const Header: React.FC<HeaderProps> = ({
  activeTab,
  setActiveTab,
  isRefreshing,
  onRefresh,
  isOnline,
}) => {
  const { theme, toggleTheme } = useTheme()
  const { playEnter, playScroll } = useSound()

  const navItems = [
    { id: 'overview' as ActiveTab, label: 'Overview', icon: LayoutDashboard },
    { id: 'services' as ActiveTab, label: 'Services', icon: Cpu },
    { id: 'diagnostics' as ActiveTab, label: 'Logs', icon: TerminalSquare },
  ]

  const navContainerRef = useRef<HTMLDivElement>(null)
  const [pillStyle, setPillStyle] = useState<{ left: number; width: number }>({
    left: 0,
    width: 0,
  })
  const navButtonRefs = useRef<Map<ActiveTab, HTMLButtonElement>>(new Map())

  useEffect(() => {
    const btn = navButtonRefs.current.get(activeTab)
    const container = navContainerRef.current
    if (btn && container) {
      const btnRect = btn.getBoundingClientRect()
      const containerRect = container.getBoundingClientRect()
      setPillStyle({
        left: btnRect.left - containerRect.left,
        width: btnRect.width,
      })
    }
  }, [activeTab])

  const handleTabChange = (tab: ActiveTab) => {
    if (tab !== activeTab) {
      playScroll()
      setActiveTab(tab)
    }
  }

  const handleRefreshClick = () => {
    playEnter()
    onRefresh()
  }

  const handleThemeToggle = () => {
    playEnter()
    toggleTheme()
  }

  return (
    <header className="fixed top-3 left-0 right-0 z-50 pointer-events-none px-4 sm:px-6 lg:px-8">
      <div className="glass-capsule pointer-events-auto mx-auto flex items-center justify-between gap-3 rounded-full px-4 sm:px-6 py-2 shadow-floating transition-colors duration-200 w-full max-w-7xl">
        {/* Brand & Connection Indicator */}
        <div className="flex items-center gap-2.5 shrink-0 flex-1 min-w-0">
          <div className="flex h-9 w-9 items-center justify-center rounded-full bg-white dark:bg-stone-900 p-1 shadow-xs border border-black/[0.05] dark:border-white/[0.08] shrink-0">
            <img src="/icons/basket-icon.svg" alt="Basket" className="h-6 w-6 object-contain" />
          </div>
          <div className="flex items-center gap-2 min-w-0">
            <span className="font-display text-base font-extrabold tracking-tight text-stone-900 dark:text-stone-50 whitespace-nowrap">
              Basket
            </span>
            <span
              className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-micro font-mono font-bold uppercase whitespace-nowrap shrink-0 ${
                isOnline
                  ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400'
                  : 'bg-rose-500/10 text-rose-600 dark:text-rose-400'
              }`}
            >
              <span
                className={`h-1.5 w-1.5 rounded-full shrink-0 ${
                  isOnline ? 'bg-emerald-500 animate-pulse' : 'bg-rose-500'
                }`}
              />
              <span className="hidden sm:inline">{isOnline ? 'Live' : 'Offline'}</span>
            </span>
          </div>
        </div>

        {/* Primary Desktop Navigation Tabs with Sliding Active Pill (Section 5.6) */}
        <nav
          ref={navContainerRef}
          className="hidden sm:flex relative items-center p-1 rounded-full bg-stone-200/40 dark:bg-stone-800/40 shrink-0"
          aria-label="Dashboard Navigation"
        >
          {/* Sliding Pill Indicator (300ms cubic-bezier(0.2, 0.8, 0.2, 1)) */}
          {pillStyle.width > 0 && (
            <div
              className="absolute top-1 bottom-1 rounded-full bg-stone-900 text-white dark:bg-stone-100 shadow-xs pointer-events-none transition-all duration-300 ease-[cubic-bezier(0.2,0.8,0.2,1)]"
              style={{
                left: `${pillStyle.left}px`,
                width: `${pillStyle.width}px`,
              }}
            />
          )}

          {navItems.map(({ id, label, icon: Icon }) => {
            const isActive = activeTab === id
            return (
              <button
                key={id}
                ref={el => {
                  if (el) navButtonRefs.current.set(id, el)
                  else navButtonRefs.current.delete(id)
                }}
                type="button"
                role="tab"
                aria-selected={isActive}
                onClick={() => handleTabChange(id)}
                className={`focus-ring relative z-10 flex items-center gap-1.5 rounded-full px-3.5 py-1.5 text-xs font-semibold font-sans whitespace-nowrap shrink-0 transition-colors duration-200 ${
                  isActive
                    ? 'text-white dark:text-stone-900'
                    : 'text-stone-600 dark:text-stone-300 hover:text-stone-900 dark:hover:text-white'
                }`}
              >
                <Icon className="h-3.5 w-3.5 shrink-0" />
                <span>{label}</span>
              </button>
            )
          })}
        </nav>

        {/* Control Actions (Refresh, Theme Toggle) - All with 48dp Touch Targets */}
        <div className="flex items-center justify-end gap-0.5 shrink-0 flex-1">
          {/* Refresh Telemetry Button */}
          <button
            type="button"
            onClick={handleRefreshClick}
            disabled={isRefreshing}
            className="focus-ring flex min-w-[40px] min-h-[40px] items-center justify-center rounded-full text-stone-600 dark:text-stone-300 hover:bg-stone-100 dark:hover:bg-stone-800 transition disabled:opacity-40"
            aria-label="Refresh telemetry and service status"
            title="Refresh status"
          >
            <RefreshCw
              className={`h-4 w-4 ${isRefreshing ? 'animate-spin text-basket-DEFAULT dark:text-basket-200' : ''}`}
            />
          </button>

          <div className="h-4 w-px bg-stone-300/60 dark:bg-stone-700/60 mx-1" aria-hidden="true" />

          {/* Theme Mode Toggle (DESIGN.md Section 2.9: Sun hover:rotate-45, Moon hover:-rotate-12) */}
          <button
            type="button"
            onClick={handleThemeToggle}
            className="focus-ring flex min-w-[40px] min-h-[40px] items-center justify-center rounded-full text-stone-600 dark:text-stone-300 hover:bg-stone-100 dark:hover:bg-stone-800 transition"
            aria-label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
            title={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
          >
            {theme === 'dark' ? (
              <Sun className="h-4 w-4 text-basket-200 transition-transform duration-200 hover:rotate-45" />
            ) : (
              <Moon className="h-4 w-4 text-basket-DEFAULT transition-transform duration-200 hover:-rotate-12" />
            )}
          </button>
        </div>
      </div>
    </header>
  )
}
