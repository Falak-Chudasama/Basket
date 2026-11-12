import React, { useState, useEffect, useCallback } from 'react'
import { Header, type ActiveTab } from './components/Header'
import { OverviewView } from './views/OverviewView'
import { ServicesView } from './views/ServicesView'
import { DiagnosticsView } from './views/DiagnosticsView'
import { api } from './api/client'
import { useToast } from './context/ToastContext'
import type { OverviewResponse, NginxStatus, RouteStatus, OperationRecord } from './types/api'

export const App: React.FC = () => {
  const { error } = useToast()
  const [activeTab, setActiveTab] = useState<ActiveTab>('overview')
  const [overview, setOverview] = useState<OverviewResponse | null>(null)
  const [nginxData, setNginxData] = useState<NginxStatus | null>(null)
  const [routesData, setRoutesData] = useState<RouteStatus[]>([])
  const [operationsData, setOperationsData] = useState<OperationRecord[]>([])
  const [selectedLogService, setSelectedLogService] = useState<string>('basket-control')

  const [isLoading, setIsLoading] = useState<boolean>(true)
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false)
  const [isOnline, setIsOnline] = useState<boolean>(true)

  // Master fetch
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

  // Fast telemetry polling (every 2.5s) when document is visible
  useEffect(() => {
    const pollInterval = setInterval(() => {
      if (document.visibilityState === 'visible') {
        api.getSystemTelemetry()
          .then(telemetry => {
            setOverview(prev => prev ? { ...prev, system: telemetry } : prev)
          })
          .catch(() => {})
      }
    }, 2500)

    return () => clearInterval(pollInterval)
  }, [])

  // Normal overview polling (every 6s)
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

  return (
    <div className="min-h-screen bg-[#F8F9F5] text-stone-900 dark:bg-[#121310] dark:text-stone-50 font-sans antialiased transition-colors duration-200">
      {/* Floating Navigation Capsule */}
      <Header
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        isRefreshing={isRefreshing}
        onRefresh={() => fetchAllData(false)}
        isOnline={isOnline}
      />

      {/* Main Container */}
      <main className="max-w-6xl mx-auto px-4 sm:px-6 pb-20">
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
        <footer className="mt-16 pt-6 border-t border-black/[0.04] dark:border-white/[0.05] text-center text-xs text-stone-400 dark:text-stone-600 font-sans">
          <p>Basket • Local Operations Control Plane</p>
        </footer>
      </main>
    </div>
  )
}
