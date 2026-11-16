import React, { createContext, useContext, useState, useCallback } from 'react'
import { CheckCircle2, AlertCircle, Info, X } from 'lucide-react'
import { playNotification, playFailed } from '../lib/sound'

export type ToastType = 'success' | 'error' | 'info'

export interface Toast {
  id: string
  type: ToastType
  title: string
  message?: string
}

interface ToastContextType {
  toast: (type: ToastType, title: string, message?: string) => void
  success: (title: string, message?: string) => void
  error: (title: string, message?: string) => void
  info: (title: string, message?: string) => void
}

const ToastContext = createContext<ToastContextType>({
  toast: () => {},
  success: () => {},
  error: () => {},
  info: () => {},
})

export const ToastProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [toasts, setToasts] = useState<Toast[]>([])

  const removeToast = useCallback((id: string) => {
    setToasts(prev => prev.filter(t => t.id !== id))
  }, [])

  const addToast = useCallback((type: ToastType, title: string, message?: string) => {
    const id = `${Date.now()}-${Math.random().toString(36).substring(2, 9)}`
    setToasts(prev => [...prev.slice(-3), { id, type, title, message }])

    // Trigger audio pairing per Section 5.9:
    // Success/info triggers playNotification(); error triggers playFailed()
    if (type === 'error') {
      playFailed()
    } else {
      playNotification()
    }

    // Auto-dismiss exact 4200ms per Section 2.9 (motion.toast) & Section 5.9
    setTimeout(() => {
      removeToast(id)
    }, 4200)
  }, [removeToast])

  const success = useCallback((title: string, message?: string) => addToast('success', title, message), [addToast])
  const error = useCallback((title: string, message?: string) => addToast('error', title, message), [addToast])
  const info = useCallback((title: string, message?: string) => addToast('info', title, message), [addToast])

  return (
    <ToastContext.Provider value={{ toast: addToast, success, error, info }}>
      {children}
      {/* Toast Notification Container (max-w-sm 384px, rounded-2xl, elevation lift) */}
      <div
        className="fixed bottom-5 right-5 z-50 flex flex-col gap-2.5 max-w-sm w-full pointer-events-none px-4 sm:px-0"
        role="region"
        aria-live="polite"
        aria-label="Notifications"
      >
        {toasts.map(t => (
          <div
            key={t.id}
            className={`pointer-events-auto flex items-start gap-3 p-3.5 rounded-2xl shadow-lift border animate-slide-up transition-all glass-panel ${
              t.type === 'success'
                ? 'border-emerald-500/30 text-stone-900 dark:text-stone-100'
                : t.type === 'error'
                ? 'border-rose-500/40 text-stone-900 dark:text-stone-100'
                : 'border-basket-500/40 dark:border-basket-400/30 text-stone-900 dark:text-stone-100'
            }`}
          >
            <div className="mt-0.5 shrink-0">
              {t.type === 'success' && <CheckCircle2 className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />}
              {t.type === 'error' && <AlertCircle className="w-5 h-5 text-rose-500 dark:text-rose-400" />}
              {t.type === 'info' && <Info className="w-5 h-5 text-basket-DEFAULT dark:text-basket-200" />}
            </div>
            <div className="flex-1 min-w-0">
              <h4 className="text-sm font-bold tracking-tight font-sans">{t.title}</h4>
              {t.message && (
                <p className="text-xs text-stone-600 dark:text-stone-400 mt-0.5 line-clamp-2 font-sans">
                  {t.message}
                </p>
              )}
            </div>
            {/* 48dp / 48px touch target button per Section 5.9 & 7.1 */}
            <button
              type="button"
              onClick={() => removeToast(t.id)}
              className="flex items-center justify-center min-w-[48px] min-h-[48px] -mr-2 -my-2 rounded-lg text-stone-400 hover:text-stone-700 dark:hover:text-stone-200 transition-colors focus-ring"
              aria-label="Dismiss notification"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  )
}

export const useToast = () => useContext(ToastContext)
