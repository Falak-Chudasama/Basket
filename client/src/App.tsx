import React, { useState, useEffect, useCallback } from 'react'
import { Header, type ActiveTab } from './components/Header'
import { FloatingBottomBar } from './components/FloatingBottomBar'
import { OverviewView } from './views/OverviewView'
import { ServicesView } from './views/ServicesView'
import { DiagnosticsView } from './views/DiagnosticsView'
import { api } from './api/client'
import { useToast } from './context/ToastContext'
import { useSound } from './context/SoundContext'
import type { OverviewResponse, NginxStatus, RouteStatus, OperationRecord } from './types/api'

const TABS: ActiveTab[] = ['overview', 'services', 'diagnostics']

export const App: React.FC = () => {
  const { error } = useToast()
  const { playScroll } = useSound()
  const [activeTab, setActiveTab] = useState<ActiveTab>('overview')
  const [overview, setOverview] = useState<OverviewResponse | null>(null)
  const [nginxData, setNginxData] = useState<NginxStatus | null>(null)
  const [routesData, setRoutesData] = useState<RouteStatus[]>([])
  const [operationsData, setOperationsData] = useState<OperationRecord[]>([])
  const [selectedLogService, setSelectedLogService] = useState<string>('basket-control')

  const [isLoading, setIsLoading] = useState<boolean>(true)
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false)
  const [isOnline, setIsOnline] = useState<boolean>(true)

  // Master telemetry and state fetch
  const fetchAllData = useCallback(async (silent: boolean = false) => {
    if (!silent) setIsRefreshing(true)
    try {
      const [ovRes, ngRes, rtRes, opRes] = await Promise.allSettled([
        api.getOverview(),
        api.getNginxStatus(),
        api.getRoutes(),
        api.getOperations(50),
      ])

      if (ovRes.status === 'fulfilled') {
        setOverview(ovRes.value)
        setIsOnline(true)
      } else {
        setIsOnline(false)
        if (!silent) error('Overview Failed', ovRes.reason.message)
      }

      if (ngRes.status === 'fulfilled') {
        setNginxData(ngRes.value)
      }

      if (rtRes.status === 'fulfilled') {
        setRoutesData(rtRes.value)
      }

      if (opRes.status === 'fulfilled') {
        setOperationsData(opRes.value)
      }
    } catch (err: any) {
      setIsOnline(false)
      if (!silent) error('Connection Error', err.message)
    } finally {
      setIsLoading(false)
      if (!silent) setIsRefreshing(false)
    }
  }, [error])

  useEffect(() => {
    fetchAllData(false)
  }, [fetchAllData])

  // Fast telemetry polling (every 2.5s) when document is active
  useEffect(() => {
    const pollInterval = setInterval(() => {
      if (document.visibilityState === 'visible') {
        api.getSystemTelemetry()
          .then(telemetry => {
            setOverview(prev => (prev ? { ...prev, system: telemetry } : prev))
          })
          .catch(() => {})
      }
    }, 2500)

    return () => clearInterval(pollInterval)
  }, [])

  // Routine full overview polling (every 6s)
  useEffect(() => {
    const pollInterval = setInterval(() => {
      if (document.visibilityState === 'visible') {
        fetchAllData(true)
      }
    }, 6000)

    return () => clearInterval(pollInterval)
  }, [fetchAllData])

  const handleViewLogs = (serviceId: string) => {
    setSelectedLogService(serviceId)
    setActiveTab('diagnostics')
  }

  // Ctrl + ArrowLeft / ArrowRight Keyboard Tab Navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Don't intercept if user is typing in an input, textarea, or select element
      if (
        e.target instanceof HTMLInputElement ||
        e.target instanceof HTMLTextAreaElement ||
        e.target instanceof HTMLSelectElement
      ) {
        return
      }

      // Support Ctrl + Left / Right (and Cmd + Left / Right on macOS)
      if (e.ctrlKey || e.metaKey) {
        if (e.key === 'ArrowRight' || e.key === 'Right') {
          e.preventDefault()
          setActiveTab(prev => {
            const currentIndex = TABS.indexOf(prev)
            const nextTab = TABS[(currentIndex + 1) % TABS.length]
            playScroll()
            return nextTab
          })
        } else if (e.key === 'ArrowLeft' || e.key === 'Left') {
          e.preventDefault()
          setActiveTab(prev => {
            const currentIndex = TABS.indexOf(prev)
            const nextTab = TABS[(currentIndex - 1 + TABS.length) % TABS.length]
            playScroll()
            return nextTab
          })
        }
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [playScroll])

  return (
    <div className="relative min-h-screen bg-[#F8F9F5] text-stone-900 dark:bg-[#121310] dark:text-stone-50 font-sans antialiased selection:bg-basket-DEFAULT/20 selection:text-basket-900 dark:selection:text-basket-100">
      {/* Ambient Refraction Orbs for Desktop Web (DESIGN.md Section 2.8) */}
      <div className="hidden lg:block pointer-events-none fixed inset-0 overflow-hidden z-0" aria-hidden="true">
        <div className="absolute -top-32 -left-32 w-[500px] h-[500px] rounded-full bg-basket-DEFAULT/4 dark:bg-basket-200/5 blur-[110px]" />
        <div className="absolute top-1/2 -right-32 w-[500px] h-[500px] rounded-full bg-basket-400/3 dark:bg-basket-DEFAULT/4 blur-[110px]" />
        <div className="absolute -bottom-32 left-1/3 w-[500px] h-[500px] rounded-full bg-basket-200/4 dark:bg-basket-200/3 blur-[110px]" />
      </div>

      {/* Pinned Stationary Floating Top Glass Capsule Navbar (DESIGN.md Section 4.1 & 5.6) */}
      <Header
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        isRefreshing={isRefreshing}
        onRefresh={() => fetchAllData(false)}
        isOnline={isOnline}
      />

      {/* Spacious Main Container (max-w-7xl with pt-20 offset for stationary fixed navbar) */}
      <main className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-20 pb-24 sm:pb-16">
        {activeTab === 'overview' && (
          <OverviewView
            overview={overview}
            nginxData={nginxData}
            onMutated={() => fetchAllData(true)}
            isLoading={isLoading}
          />
        )}

        {activeTab === 'services' && (
          <ServicesView
            services={overview?.services || []}
            onMutated={() => fetchAllData(true)}
            onViewLogs={handleViewLogs}
          />
        )}

        {activeTab === 'diagnostics' && (
          <DiagnosticsView
            services={overview?.services || []}
            routes={routesData}
            operations={operationsData}
            selectedLogService={selectedLogService}
            setSelectedLogService={setSelectedLogService}
          />
        )}

        {/* Minimal Quiet Footer */}
        <footer className="mt-16 pt-6 border-t border-black/[0.04] dark:border-white/[0.05] text-center text-caption text-stone-400 dark:text-stone-600 font-sans">
          <p>Basket • Fruit Family Operations Control Plane</p>
        </footer>
      </main>

      {/* Mobile Floating Bottom Bar Dock (< 640px viewport per Section 4.1 & 5.6) */}
      <FloatingBottomBar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
      />
    </div>
  )
}
