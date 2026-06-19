'use client'

import * as RadixToast from '@radix-ui/react-toast'
import { CheckCircle, XCircle, Info, X } from 'lucide-react'
import { createContext, useContext, useState, useCallback, type ReactNode } from 'react'
import { clsx } from 'clsx'

type ToastVariant = 'success' | 'error' | 'info'

interface ToastMessage {
  id: string
  title: string
  description?: string
  variant: ToastVariant
}

interface ToastContextValue {
  toast: (msg: Omit<ToastMessage, 'id'>) => void
}

const ToastContext = createContext<ToastContextValue | null>(null)

const icons = {
  success: <CheckCircle className="h-5 w-5 text-success" />,
  error: <XCircle className="h-5 w-5 text-danger" />,
  info: <Info className="h-5 w-5 text-blue-500" />,
}

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<ToastMessage[]>([])

  const toast = useCallback((msg: Omit<ToastMessage, 'id'>) => {
    setToasts((prev) => [...prev, { ...msg, id: crypto.randomUUID() }])
  }, [])

  const dismiss = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id))
  }, [])

  return (
    <ToastContext.Provider value={{ toast }}>
      <RadixToast.Provider swipeDirection="right">
        {children}
        {toasts.map((t) => (
          <RadixToast.Root
            key={t.id}
            open
            onOpenChange={(open) => { if (!open) dismiss(t.id) }}
            className={clsx(
              'flex items-start gap-3 rounded-lg border bg-white p-4 shadow-lg',
              'data-[state=open]:animate-in data-[state=closed]:animate-out data-[swipe=end]:animate-out',
              'data-[state=closed]:fade-out-80 data-[state=open]:slide-in-from-top-full',
            )}
          >
            {icons[t.variant]}
            <div className="flex-1 min-w-0">
              <RadixToast.Title className="text-sm font-semibold text-gray-900">{t.title}</RadixToast.Title>
              {t.description && (
                <RadixToast.Description className="mt-0.5 text-sm text-gray-600">{t.description}</RadixToast.Description>
              )}
            </div>
            <RadixToast.Close className="rounded p-0.5 hover:bg-gray-100">
              <X className="h-4 w-4 text-gray-400" />
            </RadixToast.Close>
          </RadixToast.Root>
        ))}
        <RadixToast.Viewport className="fixed top-4 right-4 z-[100] flex max-h-screen w-full max-w-sm flex-col gap-2" />
      </RadixToast.Provider>
    </ToastContext.Provider>
  )
}

export function useToast() {
  const ctx = useContext(ToastContext)
  if (!ctx) throw new Error('useToast must be used within ToastProvider')
  return ctx
}
