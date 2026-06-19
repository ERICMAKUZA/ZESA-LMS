'use client'

import * as Dialog from '@radix-ui/react-dialog'
import { X } from 'lucide-react'
import { type ReactNode } from 'react'

interface ModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  title: string
  children: ReactNode
  footer?: ReactNode
}

export default function Modal({ open, onOpenChange, title, children, footer }: ModalProps) {
  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-40 bg-black/50 data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0" />
        <Dialog.Content className="fixed left-1/2 top-1/2 z-50 w-full max-w-lg -translate-x-1/2 -translate-y-1/2 rounded-lg bg-white p-6 shadow-xl data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95">
          <div className="flex items-start justify-between mb-4">
            <Dialog.Title className="text-lg font-semibold text-gray-900">{title}</Dialog.Title>
            <Dialog.Close className="rounded p-1 hover:bg-gray-100">
              <X className="h-5 w-5 text-gray-500" />
            </Dialog.Close>
          </div>
          <div className="text-sm text-gray-700">{children}</div>
          {footer && <div className="mt-6 flex justify-end gap-3">{footer}</div>}
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  )
}
