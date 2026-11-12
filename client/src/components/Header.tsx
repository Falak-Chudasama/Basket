import React from 'react'
import { Sun, Moon, RefreshCw, LayoutDashboard, Cpu, TerminalSquare } from 'lucide-react'
import { useTheme } from '../context/ThemeContext'

export type ActiveTab = 'overview' | 'services' | 'diagnostics'

interface HeaderProps {
  activeTab: ActiveTab
  setActiveTab: (tab: ActiveTab) => void
  isRefreshing: boolean
  onRefresh: () => void
  isOnline: boolean
}

export const Header: React.FC<HeaderProps> = ({
  activeTab,
  setActiveTab,
  isRefreshing,
  onRefresh,
  isOnline,
}) => {
  const { theme, toggleTheme } = useTheme()

  const navItems = [
    { id: 'overview' as ActiveTab, label: 'Overview', icon: LayoutDashboard },
    { id: 'services' as ActiveTab, label: 'Services', icon: Cpu },
    { id: 'diagnostics' as ActiveTab, label: 'Logs', icon: TerminalSquare },
  ]

  return (
    <header className="sticky top-4 z-40 mx-auto w-full max-w-6xl px-4 sm:px-6 mb-8">
      <div className="glass-capsule flex items-center justify-between gap-3 rounded-full px-4 sm:px-5 py-2.5 shadow-floating transition-colors duration-200">
        {/* Brand & Connection Indicator */}
        <div className="flex items-center gap-2.5 shrink-0">
          <div className="flex h-9 w-9 items-center justify-center rounded-full bg-white dark:bg-stone-800 p-1 shadow-2xs border border-black/[0.05] dark:border-white/[0.08] shrink-0">
            <img src="/icons/basket-icon.svg" alt="Basket" className="h-6 w-6 object-contain" />
          </div>
          <div className="flex items-center gap-2">
            <span className="font-display text-base font-extrabold tracking-tight text-stone-900 dark:text-white whitespace-nowrap">
              Basket
            </span>
            <span
              className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[11px] font-mono font-medium whitespace-nowrap shrink-0 ${
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
              <span className="hidden sm:inline">{isOnline ? 'Online' : 'Offline'}</span>
            </span>
          </div>
        </div>

        {/* Primary Navigation Tabs */}
        <nav className="flex items-center gap-1 shrink-0" aria-label="Dashboard Navigation">
          {navItems.map(({ id, label, icon: Icon }) => {
            const isActive = activeTab === id
            return (
              <button
                key={id}
                type="button"
                onClick={() => setActiveTab(id)}
                className={`focus-ring flex items-center gap-1.5 rounded-full px-3.5 py-1.5 text-xs font-semibold font-sans whitespace-nowrap shrink-0 transition-all ${
                  isActive
                    ? 'bg-stone-900 text-white dark:bg-stone-100 dark:text-stone-900 shadow-xs'
                    : 'text-stone-600 dark:text-stone-300 hover:bg-stone-100 dark:hover:bg-stone-800 hover:text-stone-900 dark:hover:text-white'
                }`}
              >
                <Icon className="h-3.5 w-3.5 shrink-0" />
                <span>{label}</span>
              </button>
            )
          })}
        </nav>

        {/* Actions (Refresh & Dark/Light Switcher) */}
        <div className="flex items-center gap-1 shrink-0">
          <button
            type="button"
            onClick={onRefresh}
            disabled={isRefreshing}
            className="focus-ring flex h-8 w-8 items-center justify-center rounded-full text-stone-600 dark:text-stone-300 hover:bg-stone-100 dark:hover:bg-stone-800 transition disabled:opacity-40"
            aria-label="Refresh telemetry and status"
            title="Refresh"
          >
            <RefreshCw className={`h-4 w-4 ${isRefreshing ? 'animate-spin text-basket-500' : ''}`} />
          </button>

          <div className="h-4 w-px bg-stone-200 dark:bg-stone-700 mx-0.5" aria-hidden="true" />

          <button
            type="button"
            onClick={toggleTheme}
            className="focus-ring flex h-8 w-8 items-center justify-center rounded-full text-stone-600 dark:text-stone-300 hover:bg-stone-100 dark:hover:bg-stone-800 transition"
            aria-label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
            title={theme === 'dark' ? 'Light mode' : 'Dark mode'}
          >
            {theme === 'dark' ? (
              <Sun className="h-4 w-4 text-basket-400 transition-transform duration-200 hover:rotate-45" />
            ) : (
              <Moon className="h-4 w-4 text-basket-500 dark:text-basket-400 transition-transform duration-200 hover:-rotate-12" />
            )}
          </button>
        </div>
      </div>
    </header>
  )
}
